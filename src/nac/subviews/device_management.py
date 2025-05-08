from django.views.generic import ListView, DetailView
from django.views.generic.edit import UpdateView, DeleteView, CreateView, FormMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
import json
from django.http import JsonResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from django.forms.models import model_to_dict

from ..models import Device, AuthorizationGroup, DeviceRoleProd
from ..forms import DeviceForm, DeviceSearchForm, DeviceHistoryForm
from ..validation import normalize_mac


class DeviceListView(LoginRequiredMixin, ListView):
    model = Device
    template_name = "devices.html"
    context_object_name = "device_list"

    def get_queryset(self):
        # only show devices from authorization_groups the user is authorized to see
        device_list = Device.objects.filter(authorization_group__in=self.request.user.authorization_group.all())
        # filter for search results
        query = self.request.GET.get("search_string")
        if query:
            device_list = device_list.filter(
                Q(appl_NAC_Hostname__icontains=query) |
                Q(appl_NAC_macAddressAIR__icontains=normalize_mac(query)) |
                Q(appl_NAC_macAddressCAB__icontains=normalize_mac(query)) |
                Q(asset_id__icontains=query))

        # filter by authorization group
        selected_authorization_groups = self.request.GET.get("authorization_group")
        if selected_authorization_groups:
            device_list = device_list.filter(authorization_group__in=selected_authorization_groups)

        # filter by device role prod
        selected_device_roles_prod = self.request.GET.get("device_role_prod")
        if selected_device_roles_prod:
            device_list = device_list.filter(appl_NAC_DeviceRoleProd__in=selected_device_roles_prod)
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
        context["auth_group_list"] = AuthorizationGroup.objects.filter(id__in=self.request.user.authorization_group.all())
        context["device_role_prod_list"] = DeviceRoleProd.objects.all()
        context["search_form"] = DeviceSearchForm(user=self.request.user)
        return context


class DeviceDetailView(LoginRequiredMixin, DetailView):
    model = Device
    template_name = "device_detail.html"


class DeviceUpdateView(LoginRequiredMixin, UpdateView):
    model = Device
    form_class = DeviceForm
    template_name = "device_edit.html"

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


class DeviceDeleteView(LoginRequiredMixin, DeleteView):
    model = Device
    template_name = "device_delete.html"
    success_url = reverse_lazy("devices")


class DeviceCreateView(LoginRequiredMixin, CreateView):
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
            })
        return initial

    def post(self, request, *args, **kwargs):  # handles POST-Methods for new Devices
        if 'device_data' in request.POST:
            # pre-fills the DeviceForm if a device gets imported via armis
            form = self.form_class(initial=self.get_initial())
            return render(request, self.template_name, {'form': form})
        else:
            return super().post(request, *args, **kwargs)  # else no pre-fill
