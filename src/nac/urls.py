from django.urls import path
from .views import (
    HomePageView,
    DeviceListView,
    DeviceDetailView,
    DeviceUpdateView,
    DeviceDeleteView,
    DeviceCreateView,
    SecurityGroupAutocomplete,
    AreaAutocomplete,
)

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("devices/", DeviceListView.as_view(), name="devices"),
    path("devices/<int:pk>/", DeviceDetailView.as_view(), name="device_detail"),
    path("devices/<int:pk>/edit/", DeviceUpdateView.as_view(), name="device_edit"),
    path("devices/<int:pk>/delete", DeviceDeleteView.as_view(), name="device_delete"),
    path("devices/new/", DeviceCreateView.as_view(), name="device_new"),
    path("security-group-autocomplete/", SecurityGroupAutocomplete.as_view(), name="security-group-autocomplete"),
    path("area-autocomplete/", AreaAutocomplete.as_view(), name="area-autocomplete"),
]
