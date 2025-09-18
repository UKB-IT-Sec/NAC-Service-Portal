from csv import DictReader
from nac.models import Device, AdministrationGroup, DNSDomain, DeviceRoleProd
from nac.forms import DeviceForm
from django.utils import timezone
from django.db import transaction


ESSENTIAL_HEADER = [
    "AssetID",
    "Hostname",
    "Active",
    "ForceDot1X",
    "Install",
    "SyncWithLDAPAllowed",
    "AllowAccessCAB",
    "AllowAccessAIR",
    "AllowAccessVPN",
    "AllowAccessCEL",
    "DeviceRoleProd",
    "MacAddressWireless",
    "MacAddressWired",
]
DUMMY_DATA = [
    "DummyAssetID",
    "DummyHostname",
    "True",
    "False",
    "1",
    "0",
    "true",
    "false",
    "yes",
    "faaaaaalseeee",
    "DUMMY_ROLE",
    "aaaaaaaaaaaa",
    "ffffffffffff",
]


def get_devices(csv_file):
    reader = _read_csv(csv_file)
    devices = list(reader)
    return devices


def _read_csv(csv_file):
    csv_file.seek(0)
    decoded_file = csv_file.read().decode('utf-8').splitlines()
    return DictReader(decoded_file, delimiter=';')


def _check_header_format(csv_content):
    header_fields = [h.strip().casefold() for h in csv_content.fieldnames]
    essentials_lower = [key.casefold() for key in ESSENTIAL_HEADER]
    return all(key in header_fields for key in essentials_lower)


def validate_header(csv_file):
    csv_file.seek(0)
    return _check_header_format(_read_csv(csv_file))


def _format_mac(mac):
    mac = mac.upper()
    return ":".join(mac[i:i+2] for i in range(0, 12, 2))


def _modify_macs(deviceDict):
    modified_list = []
    for device in deviceDict:
        modified_device = device.copy()
        if modified_device['appl_NAC_macAddressAIR']:
            modified_device['appl_NAC_macAddressAIR'] = [
                _format_mac(mac) for mac in modified_device['appl_NAC_macAddressAIR'].split(',')
            ]
        if modified_device['appl_NAC_macAddressCAB']:
            modified_device['appl_NAC_macAddressCAB'] = [
                _format_mac(mac) for mac in modified_device['appl_NAC_macAddressCAB'].split(',')
            ]
        modified_list.append(modified_device)
    return modified_list


def _string2bool(s):
    return str(s).lower() in ['true', '1', 'yes', 'True']


def _map_device(csv_deviceData, administration_group, dns_domain, deviceroleprod):
    db_deviceObject = {
        'administration_group': administration_group.id if administration_group else None,
        'dns_domain': dns_domain.id if dns_domain else None,
        'appl_NAC_DeviceRoleProd': deviceroleprod.id if deviceroleprod else None,
        'asset_id': csv_deviceData.get('AssetID'),
        'appl_NAC_Hostname': csv_deviceData.get('Hostname'),
        'appl_NAC_Active': _string2bool(csv_deviceData.get('Active')),
        'appl_NAC_ForceDot1X': _string2bool(csv_deviceData.get('ForceDot1X')),
        'appl_NAC_Install': _string2bool(csv_deviceData.get('Install')),
        'allowLdapSync': _string2bool(csv_deviceData.get('SyncWithLDAPAllowed')),
        'appl_NAC_AllowAccessCAB': _string2bool(csv_deviceData.get('AllowAccessCAB')),
        'appl_NAC_AllowAccessAIR': _string2bool(csv_deviceData.get('AllowAccessAIR')),
        'appl_NAC_AllowAccessVPN': _string2bool(csv_deviceData.get('AllowAccessVPN')),
        'appl_NAC_AllowAccessCEL': _string2bool(csv_deviceData.get('AllowAccessCEL')),
        'appl_NAC_macAddressAIR': csv_deviceData.get('MacAddressWireless'),
        'appl_NAC_macAddressCAB': csv_deviceData.get('MacAddressWired'),
        'source': 'CSV-Import',
    }
    return db_deviceObject


def save_checked_objects_in_db(device_dicts, deviceIDList, currentUser):
    importedDeviceNames = []
    deviceIDSet = set(str(id) for id in deviceIDList)
    for device_dict in device_dicts:
        if str(device_dict.get('id')) in deviceIDSet:
            try:
                with transaction.atomic():
                    device_data = dict(device_dict)
                    device_data.pop('id', None)
                    administration_group = AdministrationGroup.objects.get(name=device_data.pop('administration_group'))
                    dns_domain = DNSDomain.objects.get(name=device_data.pop('dns_domain'))
                    deviceroleprod = DeviceRoleProd.objects.get(name=device_data.pop('appl_NAC_DeviceRoleProd'))
                    device = Device.objects.create(
                        administration_group=administration_group,
                        dns_domain=dns_domain,
                        appl_NAC_DeviceRoleProd=deviceroleprod,
                        modified_by=currentUser,
                        **device_data
                    )
                    importedDeviceNames.append(device.appl_NAC_Hostname)
            except Exception as e:
                raise Exception(f"{e} - for Device {device_dict}")
    return importedDeviceNames


def handle_devices(csv_deviceDict, administration_group, dns_domain):
    device_dicts = []
    invalid_devices = []
    for idC, csv_deviceData in enumerate(csv_deviceDict):
        try:
            deviceroleprod = DeviceRoleProd.objects.get(name=csv_deviceData.get('DeviceRoleProd'))
            db_deviceObject = _map_device(csv_deviceData, administration_group, dns_domain, deviceroleprod)
            form = DeviceForm(data=db_deviceObject)
            if form.is_valid():
                cleaned = form.cleaned_data
                cleaned['creationDate'] = timezone.localtime().isoformat(timespec='seconds')
                cleaned['id'] = idC
                cleaned['administration_group'] = administration_group.name if administration_group else None
                cleaned['dns_domain'] = dns_domain.name if dns_domain else None
                cleaned['appl_NAC_DeviceRoleProd'] = deviceroleprod.name if deviceroleprod else None
                device_dicts.append(cleaned)
            else:
                db_deviceObject['error'] = form.errors
                invalid_devices.append(db_deviceObject)
        except Exception as e:
            raise Exception(f"{e} - Device {csv_deviceData}")
    return device_dicts, invalid_devices
