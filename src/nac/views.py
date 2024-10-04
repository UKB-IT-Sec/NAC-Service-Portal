from django.views.generic import TemplateView, ListView, DetailView, View
from django.views.generic.edit import UpdateView, DeleteView, CreateView
from django.db.models import Q
from django.urls import reverse_lazy
from dal import autocomplete
from .models import Device, DeviceRoleProd, AuthorizationGroup, DeviceRoleInst
from .forms import DeviceForm
from django.core.cache import cache
from django.shortcuts import render
from helper.armis import get_armis_sites, get_devices


class HomePageView(TemplateView):
    template_name = "home.html"


class DeviceListView(ListView):
    model = Device
    template_name = "devices.html"

    def get_queryset(self):
        # only show devices from authorization_groups the user is authorized to see
        device_list = Device.objects.filter(authorization_group__in=self.request.user.authorization_group.all())
        # filter for search results
        query = self.request.GET.get("q")
        if query:
            device_list = device_list.filter(
                Q(name__icontains=query) | Q(appl_NAC_Hostname__icontains=query) |
                Q(appl_NAC_macAddressAIR__icontains=query) | Q(appl_NAC_macAddressCAB__icontains=query)
                | Q(appl_NAC_FQDN__icontains=query))
        return device_list


class ArmisView(View):
    template_name = "armis_import.html"

    def _get_context(self):
        context = {}
        armis_sites = cache.get('armis_sites')
        if armis_sites is None:
            armis_sites = get_armis_sites()
            cache.set('armis_sites', armis_sites, 3600)
        context['armis_sites'] = armis_sites
        return context

    def get(self, request, *args, **kwargs):
        context = self._get_context()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
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
    template_name = "device_new.html"
    form_class = DeviceForm


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
