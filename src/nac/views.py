from django.views.generic import TemplateView, ListView, DetailView
from django.views.generic.edit import UpdateView, DeleteView, CreateView
from django.urls import reverse_lazy

from .models import Device, DeviceForm


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

    def get_form_kwargs(self):
        kwargs = super(DeviceCreateView, self).get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs
