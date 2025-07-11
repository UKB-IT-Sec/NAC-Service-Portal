'''
    NSSP
    Copyright (C) 2024 Universitaetsklinikum Bonn AoeR

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render
from nac.forms import FileUploadForm, FileUploadSelectForm
from helper.file_integration import get_devices, handle_devices, save_checked_objects_in_db, _modify_macs
import csv
from django.http import HttpResponse
from helper.file_integration import ESSENTIAL_HEADER


class FileImportView(LoginRequiredMixin, View):
    template_name = "file_import.html"

    def get(self, request, *args, **kwargs):
        if request.GET.get("download_template") == "1":
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="import_schema.csv"'
            writer = csv.writer(response)
            header_string = ";".join(ESSENTIAL_HEADER)
            writer.writerow([header_string])
            return response

        form = FileUploadForm()
        return render(request, self.template_name, {'form': form, 'step': 1})

    def post(self, request, *args, **kwargs):
        step = int(request.POST.get('step', 1))
        context = {}
        try:
            if step == 1:
                form = FileUploadForm(request.POST, request.FILES)
                context['form'] = form
                if form.is_valid():
                    select_form = FileUploadSelectForm(request.user)
                    context['select_form'] = select_form
                    context['step'] = 2
                    devices = get_devices(request.FILES['file'])
                    request.session['devices'] = devices
                    return render(request, self.template_name, context)
                else:
                    context['step'] = 1
                    return render(request, self.template_name, context)

            elif step == 2:
                select_form = FileUploadSelectForm(request.user, request.POST)
                context['select_form'] = select_form
                context['step'] = 2
                devices = request.session.get('devices')
                if select_form.is_valid():
                    administration_group = select_form.cleaned_data["administration_group"]
                    dns_domain = select_form.cleaned_data["dns_domain"]
                    device_dicts, invalid_devices = handle_devices(devices, administration_group, dns_domain)
                    context['devices'] = _modify_macs(device_dicts)
                    context['invalid_devices'] = invalid_devices
                    request.session['devices'] = device_dicts
                return render(request, self.template_name, context)

            elif step == 3:
                device_dicts = request.session.get('devices', [])
                selected_ids = request.POST.getlist('markedForImport')
                context['step'] = 3
                context['importedDeviceList'] = save_checked_objects_in_db(device_dicts, selected_ids)
                return render(request, self.template_name, context)
        except Exception as e:
            context['error'] = e
            return render(request, self.template_name, context)
