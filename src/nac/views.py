from django.views.generic import TemplateView


class HomePageView(TemplateView):
    template_name = "home.html"

class DevicePageView(TemplateView):
    template_name = "devices.html"