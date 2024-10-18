from nac.models import Device

_mac_list = {}
_initialized = False


def _init_mac_list():
    global _mac_list, _initialized
    if not _initialized:
        devices = Device.objects.all().values('id', 'appl_NAC_macAddressCAB', 'appl_NAC_macAddressAIR')
        for device in devices:
            create_mac_list_entry(device)
        _initialized = True


def check_existing_mac(deviceObject):
    _init_mac_list()
    air_macs = deviceObject.get("appl_NAC_macAddressAIR") or ""
    cab_macs = deviceObject.get("appl_NAC_macAddressCAB") or ""

    for mac in air_macs.split(",") + cab_macs.split(","):
        if mac.strip() in _mac_list:
            return True, _mac_list[mac]

    return False, None


def create_mac_list_entry(device):
    global _mac_list
    device_id = device['id']
    air_mac = device.get("appl_NAC_macAddressAIR") or ""
    cab_macs = device.get("appl_NAC_macAddressCAB") or ""

    if air_mac.strip():
        _mac_list[air_mac.strip()] = device_id

    if cab_macs:
        _mac_list.update({mac.strip(): device_id for mac in cab_macs.split(',') if mac.strip()})
