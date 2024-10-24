from django.urls import path
from .views import (
    HomePageView,
    DeviceListView,
    DeviceDetailView,
    DeviceUpdateView,
    DeviceDeleteView,
    DeviceCreateView,
    DeviceRoleProdAutocomplete,
    DeviceRoleInstAutocomplete,
    AuthorizationGroupAutocomplete,
    AccountSettings,
    change_password,
)

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("devices/", DeviceListView.as_view(), name="devices"),
    path("devices/<int:pk>/", DeviceDetailView.as_view(), name="device_detail"),
    path("devices/<int:pk>/edit/", DeviceUpdateView.as_view(), name="device_edit"),
    path("devices/<int:pk>/delete", DeviceDeleteView.as_view(), name="device_delete"),
    path("devices/new/", DeviceCreateView.as_view(), name="device_new"),
    path("DeviceRoleProd-autocomplete/", DeviceRoleProdAutocomplete.as_view(), name="DeviceRoleProd-autocomplete"),
    path("DeviceRoleInst-autocomplete/", DeviceRoleInstAutocomplete.as_view(), name="DeviceRoleInst-autocomplete"),
    path("authorization-group-autocomplete/", AuthorizationGroupAutocomplete.as_view(), name="authorization-group-autocomplete"),
    path("account-settings/", AccountSettings.as_view(), name="account-settings"),
    path("change_password/", change_password, name='change_password'),
]
