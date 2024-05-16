from django.urls import path
from .views import HomePageView, DevicePageView

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("devices/", DevicePageView.as_view(), name="devices"),
]