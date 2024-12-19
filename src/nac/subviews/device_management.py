from django.views.generic import ListView, DetailView
from django.views.generic.edit import UpdateView, DeleteView, CreateView
from django.db.models import Q
from django.urls import reverse_lazy
from django.shortcuts import render
import json
from django.http import JsonResponse
from django.template.loader import render_to_string

from ..models import Device, AuthorizationGroup, DeviceRoleProd
from ..forms import DeviceForm, DeviceSearchForm
from ..validation import normalize_mac


class DeviceListView(ListView):
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
                Q(name__icontains=query) | Q(appl_NAC_Hostname__icontains=query) |
                Q(appl_NAC_macAddressAIR__icontains=normalize_mac(query)) |
                Q(appl_NAC_macAddressCAB__icontains=normalize_mac(query)) |
                Q(appl_NAC_FQDN__icontains=query))

        # filter by authorization group
        selected_authorization_groups = self.request.GET.get("authorization_group")
        if selected_authorization_groups:
            device_list = device_list.filter(authorization_group__in=selected_authorization_groups)

        # filter by device role prod
        selected_device_roles_prod = self.request.GET.get("device_role_prod")
        if selected_device_roles_prod:
            device_list = device_list.filter(appl_NAC_DeviceRoleProd__in=selected_device_roles_prod)
        return device_list.order_by("name")

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


class DeviceDetailView(DetailView):
    model = Device
    template_name = "device_detail.html"


class DeviceUpdateView(UpdateView):
    model = Device
    form_class = DeviceForm
    template_name = "device_edit.html"


class DeviceDeleteView(DeleteView):
    model = Device
    template_name = "device_delete.html"
    success_url = reverse_lazy("devices")


class DeviceCreateView(CreateView):
    model = Device
    form_class = DeviceForm
    template_name = "device_new.html"

    def get_initial(self):  # sets up the data for DeviceForm if a device gets imported via armis
        initial = super().get_initial()
        device_data = self.request.POST.get('device_data')
        if device_data:
            device = json.loads(device_data)
            initial.update({  # specify which attributes can/should be pre-filled
                'name': device.get('name'),
                'appl_NAC_Hostname': device.get('name'),
                'appl_NAC_macAddressCAB': device.get('macAddress'),
                'appl_NAC_FQDN': device.get('name'),
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
