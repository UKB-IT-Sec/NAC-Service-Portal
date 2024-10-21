import pytest
from unittest.mock import patch
from helper.database import MacList


@pytest.fixture
def mock_device_objects():
    return [
        {'id': 1, 'appl_NAC_macAddressCAB': '00:11:22:33:44:55', 'appl_NAC_macAddressAIR': '66:77:88:99:AA:BB'},
        {'id': 2, 'appl_NAC_macAddressCAB': 'CC:DD:EE:FF:00:11', 'appl_NAC_macAddressAIR': ''},
        {'id': 3, 'appl_NAC_macAddressCAB': '', 'appl_NAC_macAddressAIR': '22:33:44:55:66:77'},
    ]


@pytest.fixture
def mac_list():
    return MacList()


def test_get_or_create_mac_list(mac_list, mock_device_objects):
    with patch('nac.models.Device.objects.all') as mock_all:
        mock_all.return_value.values.return_value = mock_device_objects
        mac_list._get_or_create_mac_list()

        assert len(mac_list._mac_list) == 4
        assert mac_list._mac_list['00:11:22:33:44:55'] == 1
        assert mac_list._mac_list['66:77:88:99:AA:BB'] == 1
        assert mac_list._mac_list['CC:DD:EE:FF:00:11'] == 2
        assert mac_list._mac_list['22:33:44:55:66:77'] == 3
        assert mac_list._initialized is True


def test_check_existing_mac(mac_list):
    with patch.object(mac_list, '_get_or_create_mac_list'):
        mac_list._mac_list = {'00:11:22:33:44:55': 1}

        result, device_id = mac_list.check_existing_mac({'appl_NAC_macAddressCAB': '00:11:22:33:44:55'})
        assert result is True
        assert device_id == 1

        result, device_id = mac_list.check_existing_mac({'appl_NAC_macAddressCAB': 'FF:FF:FF:FF:FF:FF'})
        assert result is False
        assert device_id is None


def test_update_mac_list(mac_list):
    device = {
        'id': 1,
        'appl_NAC_macAddressCAB': '00:11:22:33:44:55, 66:77:88:99:AA:BB',
        'appl_NAC_macAddressAIR': 'CC:DD:EE:FF:00:11'
    }
    mac_list.update_mac_list(device)

    assert len(mac_list._mac_list) == 3
    assert mac_list._mac_list['00:11:22:33:44:55'] == 1
    assert mac_list._mac_list['66:77:88:99:AA:BB'] == 1
    assert mac_list._mac_list['CC:DD:EE:FF:00:11'] == 1

    assert set(mac_list._mac_list.keys()) == {'00:11:22:33:44:55', '66:77:88:99:AA:BB', 'CC:DD:EE:FF:00:11'}


def test_update_mac_list_empty_macs(mac_list):
    device = {'id': 5, 'appl_NAC_macAddressCAB': '', 'appl_NAC_macAddressAIR': ''}
    mac_list.update_mac_list(device)

    assert len(mac_list._mac_list) == 0
