from django.views.generic import ListView, DetailView
from django.views.generic.edit import UpdateView, CreateView
from django.db.models import Q
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
import json
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.forms.models import model_to_dict
from django.utils import timezone

# for csv_export
from django.http import HttpResponse
import csv
from helper.file_integration import ESSENTIAL_HEADER

from ..models import Device, AdministrationGroup, DeviceRoleProd
from ..forms import DeviceForm, DeviceSearchForm, DeviceHistoryForm
from ..validation import normalize_mac


class DeviceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = "nac.view_device"
    model = Device
    template_name = "devices.html"
    context_object_name = "device_list"

    def get_queryset(self):
        # only show devices from administration_groups the user is authorized to see
        device_list = Device.objects.filter(administration_group__in=self.request.user.administration_group.all())
        # filter for search results
        query = self.request.GET.get("search_string")
        if query:
            device_list = device_list.filter(
                Q(appl_NAC_Hostname__icontains=query) |
                Q(appl_NAC_macAddressAIR__icontains=normalize_mac(query)) |
                Q(appl_NAC_macAddressCAB__icontains=normalize_mac(query)) |
                Q(asset_id__icontains=query))

        # filter by administration group
        selected_administration_groups = self.request.GET.get("administration_group")
        if selected_administration_groups:
            device_list = device_list.filter(administration_group__in=selected_administration_groups)

        # filter by device role prod
        selected_device_roles_prod = self.request.GET.get("device_role_prod")
        if selected_device_roles_prod:
            device_list = device_list.filter(appl_NAC_DeviceRoleProd__in=selected_device_roles_prod)

        # filter for deleted devices
        deleted_selection = "active"
        if self.request.GET.get("show_deleted"):
            deleted_selection = self.request.GET.get("show_deleted")
        if (deleted_selection == "active"):
            device_list = device_list.filter(deleted=False)
        elif (deleted_selection == "deleted"):
            device_list = device_list.filter(deleted=True)

        # return results
        return device_list.order_by("appl_NAC_Hostname")

    def get(self, request, *args, **kwargs):
        # Check if the request is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Handle AJAX request by rendering only the relevant part of the template
            html = render_to_string('devices_results.html', {"device_list": self.get_queryset()})
            return JsonResponse({'html': html})

        # Otherwise, handle a normal HTTP request
        return super().get(request, *args, **kwargs)

    # we need this for the drop-down menus with filtering options
    def get_context_data(self, **kwargs):
        context = super(DeviceListView, self).get_context_data(**kwargs)
        context["admin_group_list"] = AdministrationGroup.objects.filter(id__in=self.request.user.administration_group.all())
        context["device_role_prod_list"] = DeviceRoleProd.objects.all()
        context["search_form"] = DeviceSearchForm(user=self.request.user)
        return context


class DeviceListCsvView(DeviceListView):
    def render_to_response(self, context, **response_kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="DeviceExport_{self.request.GET.get("show_deleted")}.csv"'
        writer = csv.writer(response, delimiter=';')
        header_list = ESSENTIAL_HEADER + ['Deleted']
        writer.writerow(header_list)
        for device in context['device_list']:
            writer.writerow([
                device.asset_id,
                device.appl_NAC_Hostname,
                device.appl_NAC_Active,
                device.appl_NAC_ForceDot1X,
                device.appl_NAC_Install,
                device.appl_NAC_AllowAccessCAB,
                device.appl_NAC_AllowAccessAIR,
                device.appl_NAC_AllowAccessVPN,
                device.appl_NAC_AllowAccessCEL,
                device.appl_NAC_DeviceRoleProd,
                device.appl_NAC_macAddressAIR,
                device.appl_NAC_macAddressCAB,
                device.deleted
            ])
        return response


class DeviceDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    permission_required = "nac.view_device"

    model = Device
    template_name = "device_detail.html"


class DeviceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "nac.change_device"

    model = Device
    form_class = DeviceForm
    template_name = "device_edit.html"

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        form.instance.last_modified = timezone.localtime().isoformat(timespec='seconds')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(DeviceUpdateView, self).get_context_data(**kwargs)
        # keep selected version selected in the drop down field after reloading the page
        if "device_version" in self.request.POST and self.request.POST["device_version"]:
            device_version_id = self.request.POST["device_version"]
            device_version = self.get_object().history.get(history_id=device_version_id)
        else:
            device_version = None
        context["device_history_form"] = DeviceHistoryForm(device=self.object, selected_version=device_version)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        # if no device version is selected, just show current version in device form
        if "device_version" in request.POST and not self.request.POST["device_version"]:
            return self.render_to_response(self.get_context_data(form=self.form_class(instance=self.object)))

        # preview selected version from history in form
        elif "select" in request.POST and self.request.POST["device_version"]:
            device_version_id = request.POST.get("device_version")
            device_version = self.object.history.get(history_id=device_version_id)
            form = self.form_class(initial=model_to_dict(device_version), instance=self.object)
            return self.render_to_response(self.get_context_data(form=form))

        # delete the selected version from the history
        elif "delete" in request.POST:
            device_version_id = request.POST.get("device_version")
            self.get_object().history.get(history_id=device_version_id).delete()
            return redirect(request.path)

        # save edits to device
        return super().post(request, *args, **kwargs)


class DeviceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    permission_required = "nac.delete_device"

    model = Device
    template_name = "device_delete.html"

    def post(self, request, *args, **kwargs):
        device = self.get_object()
        device.deleted = True
        device.save()
        return redirect(reverse_lazy("devices"))


class DeviceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "nac.add_device"

    model = Device
    form_class = DeviceForm
    template_name = "device_new.html"

    def _replace_Hostname_Char(self, hostname):  # replaces forbidden character in a hostname (occurs with armis imports)
        return str(hostname).replace('.', '_')

    def get_initial(self):  # sets up the data for DeviceForm if a device gets imported via armis
        initial = super().get_initial()
        device_data = self.request.POST.get('device_data')
        if device_data:
            device = json.loads(device_data)
            initial.update({  # specify which attributes can/should be pre-filled
                'asset_id': device.get('asset_id'),
                'appl_NAC_Hostname': self._replace_Hostname_Char(device.get('name')),
                'appl_NAC_macAddressCAB': device.get('macAddress'),
                'vlan': device.get('vlan'),
                'appl_NAC_Active': True,
                'appl_NAC_ForceDot1X': False,
                'appl_NAC_AllowAccessCAB': False,
                'source': 'Armis'
            })
        else:
            initial['source'] = 'Database'
        return initial

    def post(self, request, *args, **kwargs):  # handles POST-Methods for new Devices
        if 'device_data' in request.POST:
            # pre-fills the DeviceForm if a device gets imported via armis
            form = self.form_class(initial=self.get_initial())
            return render(request, self.template_name, {'form': form})
        else:
            return super().post(request, *args, **kwargs)  # else no pre-fill

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        current_time = timezone.localtime().isoformat(timespec='seconds')
        form.instance.last_modified = current_time
        form.instance.creationDate = current_time
        return super().form_valid(form)
