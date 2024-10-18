import pytest
from unittest.mock import patch
from helper.database import _init_mac_list, check_existing_mac, \
    create_mac_list_entry, _mac_list


@pytest.fixture
def mock_device_objects():
    return [
        {'id': 1, 'appl_NAC_macAddressCAB': '00:11:22:33:44:55', 'appl_NAC_macAddressAIR': '66:77:88:99:AA:BB'},
        {'id': 2, 'appl_NAC_macAddressCAB': 'CC:DD:EE:FF:00:11', 'appl_NAC_macAddressAIR': ''},
        {'id': 3, 'appl_NAC_macAddressCAB': '', 'appl_NAC_macAddressAIR': '22:33:44:55:66:77'},
    ]


@pytest.fixture(autouse=True)
def reset_mac_list_and_initialized():
    _mac_list.clear()


def test_init_mac_list(mock_device_objects):
    with patch('helper.database.Device.objects.all') as mock_all:
        mock_all.return_value.values.return_value = mock_device_objects
        _init_mac_list()

        assert len(_mac_list) == 4
        assert _mac_list['00:11:22:33:44:55'] == 1
        assert _mac_list['66:77:88:99:AA:BB'] == 1
        assert _mac_list['CC:DD:EE:FF:00:11'] == 2
        assert _mac_list['22:33:44:55:66:77'] == 3


@patch('helper.database._initialized', False)
def test_check_existing_mac():
    with patch('nac.models.Device.objects.all') as mock_all:
        mock_all.return_value.values.return_value = [
            {'id': 1, 'appl_NAC_macAddressCAB': '00:11:22:33:44:55', 'appl_NAC_macAddressAIR': ''}
        ]
        result, device_id = check_existing_mac({'appl_NAC_macAddressCAB': '00:11:22:33:44:55'})
        assert result is True
        assert device_id == 1

        result, device_id = check_existing_mac({'appl_NAC_macAddressCAB': 'FF:FF:FF:FF:FF:FF'})
        assert result is False
        assert device_id is None


def test_create_mac_list_entry():
    device = {
        'id': 1,
        'appl_NAC_macAddressCAB': '00:11:22:33:44:55, 66:77:88:99:AA:BB',
        'appl_NAC_macAddressAIR': 'CC:DD:EE:FF:00:11'
    }
    create_mac_list_entry(device)

    assert len(_mac_list) == 3
    assert _mac_list['00:11:22:33:44:55'] == 1
    assert _mac_list['66:77:88:99:AA:BB'] == 1
    assert _mac_list['CC:DD:EE:FF:00:11'] == 1

    assert set(_mac_list.keys()) == {'00:11:22:33:44:55', '66:77:88:99:AA:BB', 'CC:DD:EE:FF:00:11'}


def test_create_mac_list_entry_empty_macs():
    device = {'id': 5, 'appl_NAC_macAddressCAB': '', 'appl_NAC_macAddressAIR': ''}
    create_mac_list_entry(device)

    assert len(_mac_list) == 0
