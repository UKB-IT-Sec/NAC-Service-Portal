from django.views.generic import TemplateView, ListView
from .models import Device


class HomePageView(TemplateView):
    template_name = "home.html"

class DevicePageView(ListView):
    model = Device
    template_name = "devices.html"