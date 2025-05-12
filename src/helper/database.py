from nac.models import Device
from nac.validation import normalize_mac


class MacList:
    def __init__(self):
        self._mac_list = {}
        self._initialized = False

    def _get_or_create_mac_list(self):
        if not self._initialized:
            devices = Device.objects.all().values('id', 'appl_NAC_macAddressCAB', 'appl_NAC_macAddressAIR')
            for device in devices:
                self.update_mac_list(device)
            self._initialized = True

    def check_existing_mac(self, deviceObject):
        self._get_or_create_mac_list()
        air_macs = deviceObject.get("appl_NAC_macAddressAIR") or ""
        cab_macs = deviceObject.get("appl_NAC_macAddressCAB") or ""
        armis_macs = deviceObject.get("macAddress") or ""
        for mac in air_macs.split(",") + cab_macs.split(",") + armis_macs.split(","):
            normalized_mac = normalize_mac(mac.strip())
            if normalized_mac in self._mac_list:
                return True, self._mac_list[normalized_mac]

        return False, None

    def update_mac_list(self, device):
        device_id = device['id']
        air_macs = device.get("appl_NAC_macAddressAIR") or ""
        cab_macs = device.get("appl_NAC_macAddressCAB") or ""

        if air_macs:
            self._mac_list.update({mac.strip(): device_id for mac in air_macs.split(',') if mac.strip()})

        if cab_macs:
            self._mac_list.update({mac.strip(): device_id for mac in cab_macs.split(',') if mac.strip()})
