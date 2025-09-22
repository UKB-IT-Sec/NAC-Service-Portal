import pytest
import io
from unittest.mock import MagicMock, patch

from helper import file_integration
from nac.models import AdministrationGroup, DNSDomain, DeviceRoleProd


@pytest.mark.parametrize("mac,expected", [
    ("aabbccddeeff", "AA:BB:CC:DD:EE:FF"),
    ("AABBCCDDEEFF", "AA:BB:CC:DD:EE:FF"),
])
def test_format_mac(mac, expected):
    assert file_integration._format_mac(mac) == expected


def test_modify_macs():
    device_dict = [{
        'appl_NAC_macAddressAIR': "aabbccddeeff,112233445566",
        'appl_NAC_macAddressCAB': "ffeeddccbbaa,665544332211",
    }]
    result = file_integration._modify_macs(device_dict)
    assert result[0]['appl_NAC_macAddressAIR'] == ["AA:BB:CC:DD:EE:FF", "11:22:33:44:55:66"]
    assert result[0]['appl_NAC_macAddressCAB'] == ["FF:EE:DD:CC:BB:AA", "66:55:44:33:22:11"]


def test_read_csv_and_get_devices():
    csv_content = (
        "AssetID;Hostname;Active;ForceDot1X;Install;SyncWithLDAPAllowed;AllowAccessCAB;AllowAccessAIR;AllowAccessVPN;AllowAccessCEL;DeviceRoleProd;MacAddressWireless;MacAddressWired\n"
        "1;host1;1;0;1;1;1;1;0;0;Role1;aabbccddeeff;ffeeddccbbaa\n"
    )
    file = io.BytesIO(csv_content.encode("utf-8"))
    devices = file_integration.get_devices(file)
    assert isinstance(devices, list)
    assert devices[0]['AssetID'] == "1"
    assert devices[0]['Hostname'] == "host1"


def test_check_header_format_true():
    csv_content = io.StringIO(
        "AssetID;Hostname;Active;ForceDot1X;Install;SyncWithLDAPAllowed;AllowAccessCAB;AllowAccessAIR;AllowAccessVPN;AllowAccessCEL;DeviceRoleProd;MacAddressWireless;MacAddressWired\n"
    )
    reader = file_integration.DictReader(csv_content, delimiter=';')
    assert file_integration._check_header_format(reader)


def test_check_header_format_false():
    csv_content = io.StringIO("foo;bar;baz\n")
    reader = file_integration.DictReader(csv_content, delimiter=';')
    assert not file_integration._check_header_format(reader)[0]


def test_validate_header_true():
    csv_content = (
        "AssetID;Hostname;Active;ForceDot1X;Install;SyncWithLDAPAllowed;AllowAccessCAB;AllowAccessAIR;AllowAccessVPN;AllowAccessCEL;DeviceRoleProd;MacAddressWireless;MacAddressWired\n"
    )
    file = io.BytesIO(csv_content.encode("utf-8"))
    assert file_integration.validate_header(file)[0]


def test_validate_header_false():
    csv_content = "foo;bar;baz\n"
    file = io.BytesIO(csv_content.encode("utf-8"))
    assert not file_integration.validate_header(file)[0]


def test_map_device():
    csv_data = {
        'AssetID': '1',
        'Hostname': 'host1',
        'Active': '1',
        'ForceDot1X': '1',
        'Install': '0',
        'SyncWithLDAPAllowed': '1',
        'AllowAccessCAB': '1',
        'AllowAccessAIR': '0',
        'AllowAccessVPN': '1',
        'AllowAccessCEL': '0',
        'DeviceRoleProd': 'Role1',
        'MacAddressWireless': 'aabbccddeeff',
        'MacAddressWired': 'ffeeddccbbaa',
    }
    admin_group = MagicMock(id=42)
    dns_domain = MagicMock(id=43)
    deviceroleprod = MagicMock(id=44)
    mapped = file_integration._map_device(csv_data, admin_group, dns_domain, deviceroleprod)
    assert mapped['administration_group'] == 42
    assert mapped['dns_domain'] == 43
    assert mapped['appl_NAC_DeviceRoleProd'] == 44
    assert mapped['asset_id'] == '1'
    assert mapped['appl_NAC_Hostname'] == 'host1'


@pytest.mark.django_db
@patch("nac.forms.DeviceForm")
@patch("nac.models.DeviceRoleProd.objects.get")
def test_handle_devices_valid(mock_get_role, mock_form):
    admin_group = AdministrationGroup.objects.create(name="AG1")
    dns_domain = DNSDomain.objects.create(name="DNS1")
    deviceroleprod = DeviceRoleProd.objects.create(name="Role1")
    admin_group.DeviceRoleProd.set([deviceroleprod])
    mock_get_role.return_value = deviceroleprod

    csv_deviceDict = [{
        'AssetID': '1',
        'Hostname': 'host1',
        'Active': '1',
        'ForceDot1X': '1',
        'Install': '0',
        'SyncWithLDAPAllowed': '1',
        'AllowAccessCAB': '1',
        'AllowAccessAIR': '0',
        'AllowAccessVPN': '1',
        'AllowAccessCEL': '0',
        'DeviceRoleProd': 'Role1',
        'MacAddressWireless': 'aabbccddeeff',
        'MacAddressWired': 'ffeeddccbbaa',
    }]
    form_instance = MagicMock()
    form_instance.is_valid.return_value = True
    form_instance.cleaned_data = {'foo': 'bar'}
    mock_form.return_value = form_instance

    devices, invalid = file_integration.handle_devices(csv_deviceDict, admin_group, dns_domain)
    assert len(devices) == 1
    assert devices[0]['appl_NAC_Hostname'] == 'host1'
    assert invalid == []


@pytest.mark.django_db
@patch("nac.forms.DeviceForm")
@patch("nac.models.DeviceRoleProd.objects.get")
def test_handle_devices_invalid(mock_get_role, mock_form):
    admin_group = AdministrationGroup.objects.create(name="AG1")
    dns_domain = DNSDomain.objects.create(name="DNS1")
    deviceroleprod = DeviceRoleProd.objects.create(name="Role1")
    mock_get_role.return_value = deviceroleprod

    csv_deviceDict = [{
        'AssetID': '1',
        'Hostname': 'host1',
        'Active': '1',
        'ForceDot1X': '1',
        'Install': '0',
        'SyncWithLDAPAllowed': '1',
        'AllowAccessCAB': '1',
        'AllowAccessAIR': '0',
        'AllowAccessVPN': '1',
        'AllowAccessCEL': '0',
        'DeviceRoleProd': 'Role1',
        'MacAddressWireless': 'aabbccddeeff',
        'MacAddressWired': 'ffeeddccbbaa',
    }]
    form_instance = MagicMock()
    form_instance.is_valid.return_value = False
    form_instance.errors = {'test': 'error'}
    mock_form.return_value = form_instance

    devices, invalid = file_integration.handle_devices(csv_deviceDict, admin_group, dns_domain)
    assert devices == []
    assert len(invalid) == 1
    assert invalid[0]['error'].values()


@pytest.mark.django_db
@patch("nac.forms.DeviceForm")
@patch("nac.models.DeviceRoleProd.objects.get")
def test_handle_devices_valid_exception(mock_get_role, mock_form):
    admin_group = AdministrationGroup.objects.create(name="AG1")
    dns_domain = DNSDomain.objects.create(name="DNS1")
    deviceroleprod = DeviceRoleProd.objects.create(name="Role1")
    admin_group.DeviceRoleProd.set([deviceroleprod])
    mock_get_role.return_value = deviceroleprod

    csv_deviceDict = [{
        'AssetID': '1',
        'Hostname': 'host1',
        'Active': '1',
        'ForceDot1X': '1',
        'Install': '0',
        'SyncWithLDAPAllowed': '1',
        'AllowAccessCAB': '1',
        'AllowAccessAIR': '0',
        'AllowAccessVPN': '1',
        'AllowAccessCEL': '0',
        'DeviceRoleProd': 'Role1',
        'MacAddressWireless': 'aabbccddeeff',
        'MacAddressWired': 'ffeeddccbbaa',
    }]
    form_instance = MagicMock()
    form_instance.is_valid.return_value = True
    form_instance.cleaned_data = {'foo': 'bar'}
    mock_form.return_value = form_instance
    mock_get_role.side_effect = Exception("Error")
    with pytest.raises(Exception) as e:
        file_integration.handle_devices(csv_deviceDict, admin_group, dns_domain)
    assert 'Device' in str(e.value)


@pytest.mark.django_db
@patch("nac.models.AdministrationGroup.objects.get")
@patch("nac.models.DNSDomain.objects.get")
@patch("nac.models.DeviceRoleProd.objects.get")
@patch("nac.models.Device.objects.create")
def test_save_checked_objects_in_db(mock_create, mock_get_role, mock_get_dns, mock_get_admin):
    device_dicts = [{
        'id': 1,
        'administration_group': 'AG1',
        'dns_domain': 'DNS1',
        'appl_NAC_DeviceRoleProd': 'Role1',
        'appl_NAC_Hostname': 'host1',
    }]
    deviceIDList = [1]
    admin_group = MagicMock()
    dns_domain = MagicMock()
    deviceroleprod = MagicMock()
    device = MagicMock(appl_NAC_Hostname='host1')
    mock_get_admin.return_value = admin_group
    mock_get_dns.return_value = dns_domain
    mock_get_role.return_value = deviceroleprod
    mock_create.return_value = device
    mock_currentUser = 'DummyUser'
    names = file_integration.save_checked_objects_in_db(device_dicts, deviceIDList, mock_currentUser)
    assert names == ['host1']


@pytest.mark.django_db
@patch("nac.models.AdministrationGroup.objects.get")
@patch("nac.models.DNSDomain.objects.get")
@patch("nac.models.DeviceRoleProd.objects.get")
@patch("nac.models.Device.objects.create")
def test_save_checked_objects_in_db_exception(mock_create, mock_get_role, mock_get_dns, mock_get_admin):
    device_dicts = [{
        'id': 1,
        'administration_group': 'AG1',
        'dns_domain': 'DNS1',
        'appl_NAC_DeviceRoleProd': 'Role1',
        'appl_NAC_Hostname': 'host1',
    }]
    deviceIDList = [1]
    admin_group = MagicMock()
    dns_domain = MagicMock()
    deviceroleprod = MagicMock()
    device = MagicMock(appl_NAC_Hostname='host1')
    mock_get_admin.return_value = admin_group
    mock_get_dns.return_value = dns_domain
    mock_get_role.return_value = deviceroleprod
    mock_create.return_value = device
    mock_create.side_effect = Exception("Error")
    mock_currentUser = 'DummyUser'
    with pytest.raises(Exception) as e:
        file_integration.save_checked_objects_in_db(device_dicts, deviceIDList, mock_currentUser)
    assert 'for Device' in str(e.value)
