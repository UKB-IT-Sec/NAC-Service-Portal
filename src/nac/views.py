from django.views.generic import TemplateView, ListView, DetailView
from django.views.generic.edit import UpdateView, DeleteView, CreateView
from django.urls import reverse_lazy
from dal import autocomplete

from .models import Device, DeviceForm, SecurityGroup, Area


class HomePageView(TemplateView):
    template_name = "home.html"


class DeviceListView(ListView):
    model = Device
    template_name = "devices.html"

    def get_queryset(self):
        return Device.objects.filter(area__in=self.request.user.area.all())


class DeviceDetailView(DetailView):
    model = Device
    template_name = "device_detail.html"


class DeviceUpdateView(UpdateView):
    model = Device
    form_class = DeviceForm
    template_name = "device_edit.html"

    def get_form_kwargs(self):
        kwargs = super(DeviceUpdateView, self).get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class DeviceDeleteView(DeleteView):
    model = Device
    template_name = "device_delete.html"
    success_url = reverse_lazy("devices")


class DeviceCreateView(CreateView):
    model = Device
    template_name = "device_new.html"
    form_class = DeviceForm


class SecurityGroupAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return SecurityGroup.objects.none()

        qs = SecurityGroup.objects.all()

        #autocomplete search results
        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        #only show security groups compatible with selected area
        area_pk = self.forwarded.get("area", None)
        if area_pk:
            area = Area.objects.get(pk=area_pk)
            qs = qs.filter(id__in=area.security_group.all())

        return qs


class AreaAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Area.objects.none()

        qs = Area.objects.all()

        # only show areas compatible with user
        qs = qs.filter(id__in=self.request.user.area.all())

        #autocomplete search results
        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs

