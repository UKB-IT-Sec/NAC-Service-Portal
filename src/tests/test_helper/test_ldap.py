from ldap3 import Server, Connection, MOCK_SYNC

from nac.models import Device
from helper.ldap import map_device_data, device_exists, delete_device
from helper.filesystem import get_resources_directory

TEST_SERVER_INFO = get_resources_directory() / 'test_ldap_server_info.json'
TEST_SERVER_SCHEMA = get_resources_directory() / 'test_ldap_server_schema.json'
TEST_SERVER_DATA = get_resources_directory() / 'test_ldap_server_data.json'
SEARCH_BASE = 'ou=Devices,dc=ukbonn,dc=de'


def _setup_test_server():
    server = Server.from_definition('test_server', TEST_SERVER_INFO.__str__(), TEST_SERVER_SCHEMA.__str__())
    connection = Connection(server, user='cn=my_user,ou=test,o=lab', password='my_password', client_strategy=MOCK_SYNC)
    connection.strategy.entries_from_json(TEST_SERVER_DATA)
    connection.bind()
    return connection


def test_map_device_data():
    test_device = Device()
    result = map_device_data(test_device)
    assert isinstance(result, dict)
    assert len(result) == 13
    test_device.appl_NAC_macAddressCAB = 'aabbccddeeff'
    result = map_device_data(test_device)
    assert len(result) == 14
    assert result['appl-NAC-macAddressCAB'] == 'aabbccddeeff'


def test_device_exists():
    connection = _setup_test_server()

    assert not device_exists('NoneExistingDevice', connection, SEARCH_BASE)
    assert device_exists('testDeviceCable.ukbonn.de', connection, SEARCH_BASE)

    connection.unbind()


def test_delete_device():
    connection = _setup_test_server()
    assert device_exists('testDeviceCable.ukbonn.de', connection, SEARCH_BASE)

    delete_device('testDeviceCable.ukbonn.de', connection, SEARCH_BASE)

    assert not device_exists('testDeviceCable.ukbonn.de', connection, SEARCH_BASE)
