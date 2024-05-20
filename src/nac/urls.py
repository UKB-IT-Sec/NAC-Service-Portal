from django.urls import path
from .views import (
    HomePageView,
    DevicePageView,
    DeviceDetailView,
    DeviceUpdateView,
    DeviceDeleteView,
)

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("devices/", DevicePageView.as_view(), name="devices"),
    path("devices/<int:pk>/", DeviceDetailView.as_view(), name="device_detail"),
    path("devices/<int:pk>/edit/", DeviceUpdateView.as_view(), name="device_edit"),
    path("devices/<int:pk>/delete", DeviceDeleteView.as_view(), name="device_delete"),
]
