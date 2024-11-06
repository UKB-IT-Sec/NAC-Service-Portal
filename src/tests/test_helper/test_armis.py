import pytest
from unittest.mock import patch, MagicMock
from helper.armis import (
    armiscloud,
    _filter_sort_sites,
    get_armis_sites,
    _remove_existing_devices,
    get_devices, get_tenant_url,
)


@pytest.fixture
def mock_config():
    return {
        'armis-server': {
            'api_secret_key': 'test_key',
            'tenant_hostname': 'test_host',
            'sites_pattern': 'Site\\d+',  # 'Site' + one or more numeric id's
            'vlan_blacklist': '100,200'
        }
    }


@pytest.fixture
def mock_armis_cloud():
    return MagicMock()


@patch('helper.armis.armis_config', new_callable=MagicMock)
@patch('helper.armis.ArmisCloud')
def test_armiscloud_decorator(mock_armis_cloud, mock_armis_config, mock_config):
    mock_armis_config.__getitem__.return_value = mock_config['armis-server']
    mock_armis_cloud_instance = mock_armis_cloud.return_value

    @armiscloud
    def test_func(acloud):
        return acloud

    result = test_func()
    assert result == mock_armis_cloud_instance
    mock_armis_cloud.assert_called_once_with(
        api_secret_key='test_key',
        tenant_hostname='test_host'
    )

    result2 = test_func()
    assert result2 == result  # check if it's the same Cloud
    assert mock_armis_cloud.call_count == 1


def test_filter_sort_sites(mock_config):
    sites = {
        '1': {'name': 'Site1'},
        '2': {'name': 'Site2'},
        '3': {'name': 'OtherPatternSite'},
        '4': {'name': 'Site3'}
    }
    with patch('helper.armis.armis_config', mock_config):
        result = _filter_sort_sites(sites)
    assert list(result.keys()) == ['1', '2', '4']
    assert [site['name'] for site in result.values()] == ['Site1', 'Site2', 'Site3']


@patch('helper.armis._filter_sort_sites')
def test_get_armis_sites(mock_filter_sort_sites):
    mock_sites = {'1': {'name': 'Site1'}}
    mock_armis_cloud = MagicMock()
    mock_armis_cloud.get_sites.return_value = mock_sites
    mock_filter_sort_sites.return_value = mock_sites
    #  manually call original function without decorator to prevent argument error
    result = get_armis_sites.__wrapped__(mock_armis_cloud)

    assert result == mock_sites
    mock_armis_cloud.get_sites.assert_called_once()
    mock_filter_sort_sites.assert_called_once_with(mock_sites)


@patch('helper.armis.MacList')
def test_remove_existing_devices(mock_mac_list):
    mock_mac_list_instance = mock_mac_list.return_value
    mock_mac_list_instance.check_existing_mac.side_effect = [(True, None), (False, None), (True, None)]

    devices = [{'name': 'Device1'}, {'name': 'Device2'}, {'name': 'Device3'}]
    result = _remove_existing_devices(devices)
    assert result == [{'name': 'Device2'}]


@patch('helper.armis._remove_existing_devices')
def test_get_devices(mock_remove_existing_devices, mock_config):
    mock_devices = [{'id': '1', 'name': 'Device1'}]
    mock_armis_cloud = MagicMock()
    mock_armis_cloud.get_devices.return_value = mock_devices
    mock_remove_existing_devices.return_value = mock_devices

    #  manually call original function without decorator to prevent argument error
    with patch('helper.armis.armis_config', mock_config):
        result = get_devices.__wrapped__(mock_armis_cloud, {'name': 'TestSite'})

    assert result == mock_devices
    mock_armis_cloud.get_devices.assert_called_once_with(
        asq='in:devices site:"TestSite" timeFrame:"7 Days" !networkInterface:(vlans:100,200)',
        fields_wanted=['id', 'ipAddress', 'macAddress', 'name', 'boundaries']
    )
    mock_remove_existing_devices.assert_called_once_with(mock_devices)


def test_get_tenent_url(mock_config):
    with patch('helper.armis.armis_config', mock_config):
        assert get_tenant_url() == "https://test_host"
