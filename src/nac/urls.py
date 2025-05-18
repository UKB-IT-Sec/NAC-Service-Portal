from django.urls import path
from .subviews.home import HomePageView

from .subviews.device_management import (
    DeviceListView,
    DeviceDetailView,
    DeviceUpdateView,
    DeviceDeleteView,
    DeviceCreateView,
)

from .subviews.autocomplete import (
    DNSDomainAutocomplete,
    DeviceRoleProdAutocomplete,
    AuthorizationGroupAutocomplete,
)

from .subviews.account import (
    AccountSettings,
    change_password,
)

from .subviews.armis import ArmisView


urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("devices/", DeviceListView.as_view(), name="devices"),
    path("devices/<int:pk>/", DeviceDetailView.as_view(), name="device_detail"),
    path("devices/<int:pk>/edit/", DeviceUpdateView.as_view(), name="device_edit"),
    path("devices/<int:pk>/delete", DeviceDeleteView.as_view(), name="device_delete"),
    path("devices/new/", DeviceCreateView.as_view(), name="device_new"),
    path("armis/", ArmisView.as_view(), name="armis_import"),
    path("dns_domain-autocomplete/", DNSDomainAutocomplete.as_view(), name="dns_domain-autocomplete"),
    path("DeviceRoleProd-autocomplete/", DeviceRoleProdAutocomplete.as_view(), name="DeviceRoleProd-autocomplete"),
    path("authorization-group-autocomplete/", AuthorizationGroupAutocomplete.as_view(), name="authorization-group-autocomplete"),
    path("account-settings/", AccountSettings.as_view(), name="account-settings"),
    path("change_password/", change_password, name='change_password'),
]
