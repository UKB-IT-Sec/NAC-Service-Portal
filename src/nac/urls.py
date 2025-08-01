from django.urls import path
from .subviews.home import HomePageView

from .subviews.device_management import (
    DeviceListView,
    DeviceListCsvView,
    DeviceDetailView,
    DeviceUpdateView,
    DeviceDeleteView,
    DeviceCreateView,
)

from .subviews.autocomplete import (
    DNSDomainAutocomplete,
    DeviceRoleProdAutocomplete,
    AdministrationGroupAutocomplete,
)

from .subviews.account import (
    AccountSettings,
    change_password,
)

from .subviews.armis import ArmisView
from .subviews.file_import import FileImportView


urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("devices/", DeviceListView.as_view(), name="devices"),
    path("devices/export", DeviceListCsvView.as_view(), name="device_export_csv"),
    path("devices/<int:pk>/", DeviceDetailView.as_view(), name="device_detail"),
    path("devices/<int:pk>/edit/", DeviceUpdateView.as_view(), name="device_edit"),
    path("devices/<int:pk>/delete", DeviceDeleteView.as_view(), name="device_delete"),
    path("devices/new/", DeviceCreateView.as_view(), name="device_new"),
    path("armis/", ArmisView.as_view(), name="armis_import"),
    path("file_import/", FileImportView.as_view(), name="file_import"),
    path("dns_domain-autocomplete/", DNSDomainAutocomplete.as_view(), name="dns_domain-autocomplete"),
    path("DeviceRoleProd-autocomplete/", DeviceRoleProdAutocomplete.as_view(), name="DeviceRoleProd-autocomplete"),
    path("administration-group-autocomplete/", AdministrationGroupAutocomplete.as_view(), name="administration-group-autocomplete"),
    path("account-settings/", AccountSettings.as_view(), name="account-settings"),
    path("change_password/", change_password, name='change_password'),
]
