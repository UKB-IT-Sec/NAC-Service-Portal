from django.views.generic import TemplateView, ListView, DetailView, View
from django.views.generic.edit import UpdateView, DeleteView, CreateView
from django.db.models import Q
from django.urls import reverse_lazy
from dal import autocomplete
from .models import Device, DeviceRoleProd, AuthorizationGroup, DeviceRoleInst
from django.core.cache import cache
from helper.armis import get_armis_sites, get_devices
from .forms import DeviceForm, DeviceSearchForm
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect
import json


class HomePageView(TemplateView):
    template_name = "home.html"


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
                Q(appl_NAC_macAddressAIR__icontains=query) | Q(appl_NAC_macAddressCAB__icontains=query)
                | Q(appl_NAC_FQDN__icontains=query))

        # filter by authorization group
        selected_authorization_groups = self.request.GET.get("authorization_group")
        if selected_authorization_groups:
            device_list = device_list.filter(authorization_group__in=selected_authorization_groups)

        # filter by device role prod
        selected_device_roles_prod = self.request.GET.get("device_role_prod")
        if selected_device_roles_prod:
            device_list = device_list.filter(appl_NAC_DeviceRoleProd__in=selected_device_roles_prod)
        return device_list.order_by("name")

    # we need this for the drop-down menus with filtering options
    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(DeviceListView, self).get_context_data(**kwargs)
        context["auth_group_list"] = AuthorizationGroup.objects.filter(id__in=self.request.user.authorization_group.all())
        context["device_role_prod_list"] = DeviceRoleProd.objects.all()
        context["search_form"] = DeviceSearchForm(user=self.request.user)
        return context


class ArmisView(View):
    template_name = "armis_import.html"

    def _get_context(self):  # sets the site-context for armis_import.html, uses cache to be less time consuming
        context = {}
        armis_sites = cache.get('armis_sites')
        if armis_sites is None:
            armis_sites = get_armis_sites()
            cache.set('armis_sites', armis_sites, 3600)
        context['armis_sites'] = armis_sites
        return context

    def get(self, request, *args, **kwargs):  # rendering the html base with site-context
        context = self._get_context()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):  # gets site-id chosen in html-dropdown, gets Devices based on site-id, shows them via device-context
        context = self._get_context()

        selected_site = request.POST.get('site-id')
        context['selected_site'] = selected_site if selected_site else ''
        if selected_site:
            context['devices'] = get_devices(context['armis_sites'][selected_site])

        return render(request, self.template_name, context)


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
            form = self.form_class(initial=self.get_initial())  # pre-fills the DeviceForm if a device gets imported via armis
            return render(request, self.template_name, {'form': form})
        else:
            return super().post(request, *args, **kwargs)  # else no pre-fill


class DeviceRoleProdAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return DeviceRoleProd.objects.none()

        qs = DeviceRoleProd.objects.all().order_by('id')

#        autocomplete search results
        if self.q:
            qs = qs.filter(name__istartswith=self.q)

#        only show DeviceRoleProd compatible with selected authorization_group
        authorization_group_pk = self.forwarded.get("authorization_group", None)

        if authorization_group_pk:
            authorization_group = AuthorizationGroup.objects.get(pk=authorization_group_pk)
            qs = qs.filter(id__in=authorization_group.DeviceRoleProd.all())

        return qs


class DeviceRoleInstAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return DeviceRoleInst.objects.none()

        qs = DeviceRoleInst.objects.all().order_by('id')

        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        authorization_group_pk = self.forwarded.get("authorization_group", None)
        if authorization_group_pk:
            authorization_group = AuthorizationGroup.objects.get(pk=authorization_group_pk)
            qs = qs.filter(id__in=authorization_group.DeviceRoleInst.all())
        return qs


class AuthorizationGroupAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return AuthorizationGroup.objects.none()

        qs = AuthorizationGroup.objects.all().order_by('id')

#        only show authorization_groups compatible with user
        qs = qs.filter(id__in=self.request.user.authorization_group.all())

#        autocomplete search results
        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs


class AccountSettings(TemplateView):
    template_name = "account_settings.html"


def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('change_password')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', {
        'form': form
    })
