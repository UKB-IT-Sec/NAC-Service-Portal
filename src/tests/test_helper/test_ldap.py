from nac.models import Device
from helper.ldap import map_device_data


def test_map_device_data():
    test_device = Device()
    result = map_device_data(test_device)
    assert isinstance(result, dict)
    assert len(result) == 9
    test_device.appl_NAC_macAddressCAB = 'aabbccddeeff'
    result = map_device_data(test_device)
    assert len(result) == 10
    assert result['appl-NAC-macAddressCAB'] == 'aabbccddeeff'
