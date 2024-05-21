from django.views.generic import TemplateView, ListView, DetailView
from django.views.generic.edit import UpdateView, DeleteView, CreateView
from django.urls import reverse_lazy
from .models import Device


class HomePageView(TemplateView):
    template_name = "home.html"


class DevicePageView(ListView):
    model = Device
    template_name = "devices.html"


class DeviceDetailView(DetailView):
    model = Device
    template_name = "device_detail.html"


class DeviceUpdateView(UpdateView):
    model = Device
    fields = ("name", "area", "security_group",)
    template_name = "device_edit.html"

class DeviceDeleteView(DeleteView):
    model = Device
    template_name = "device_delete.html"
    success_url = reverse_lazy("devices")

class DeviceCreateView(CreateView):
    model = Device
    template_name = "device_new.html"
    fields = (
        "name",
        "area",
        "security_group",
    )
