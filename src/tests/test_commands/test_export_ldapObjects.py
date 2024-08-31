import pytest
from nac.management.commands.export_ldapObjects import Command, \
    CSV_SAVE_FILE, DEFAULT_OBJECT, DEFAULT_CONFIG
from unittest.mock import patch, mock_open, MagicMock
from configparser import ConfigParser
from ldap3 import SUBTREE


@pytest.fixture
def command():
    return Command()


def test_add_arguments(command):
    mock_parser = MagicMock()
    command.add_arguments(mock_parser)
    mock_parser.add_argument.assert_any_call(
        '-c', '--config_file', default=DEFAULT_CONFIG,
        help='use a specific config file [src/export.cnf]')
    mock_parser.add_argument.assert_any_call(
        '-o', '--objectclass', default=DEFAULT_OBJECT,
        help='specify which object to export')


@patch('nac.management.commands.export_ldapObjects.setup_console_logger')
@patch('nac.management.commands.export_ldapObjects.get_config_from_file')
@patch('nac.management.commands.export_ldapObjects.connect_to_ldap_server')
@patch('nac.management.commands.export_ldapObjects.Command._clear_file')
@patch('nac.management.commands.export_ldapObjects.Command._get_objects')
@patch('nac.management.commands.export_ldapObjects.Command._handle_objects')
def test_handle(mock_handle_objects, mock_get_objects, mock_clear_file,
                mock_connect_to_ldap, mock_get_config, mock_setup_logger,
                command):
    options = {
        'verbosity': 0,
        'config_file': 'test.cnf',
        'objectclass': 'testObject'
    }
    mock_config = ConfigParser()
    mock_config['ldap-server'] = {
        'address': 'test_address',
        'user': 'test_user',
        'password': 'test_password',
        'port': '389',
        'tls': 'False'
    }
    print(mock_config)
    mock_get_config.return_value = mock_config
    command.handle(**options)
    mock_setup_logger.assert_called_once_with(0)
    mock_get_config.assert_called_once_with('test.cnf')
    mock_clear_file.assert_called_once()
    mock_connect_to_ldap.assert_called_once_with(
        'test_address', 'test_user', 'test_password', port=389, tls=False
    )
    mock_get_objects.assert_called_once()
    mock_handle_objects.assert_called_once()
    assert command.config == mock_config
    assert command.objectClass == 'testObject'


@patch('nac.management.commands.export_ldapObjects.Command.write_object')
def test_handle_objects(mock_write_object, command):
    mock_entry1 = MagicMock()
    mock_entry1.entry_attributes_as_dict = {'attr1': 'value1'}
    mock_entry2 = MagicMock()
    mock_entry2.entry_attributes_as_dict = {'attr2': 'value2'}
    command.ldap_connection = MagicMock()
    command.ldap_connection.entries = [mock_entry1, mock_entry2]
    command._handle_objects()
    assert mock_write_object.call_count == 2
    mock_write_object.assert_any_call({'attr1': 'value1'}, 1)
    mock_write_object.assert_any_call({'attr2': 'value2'}, 2)


@patch('nac.management.commands.export_ldapObjects.logging')
def test_get_objects_found(mock_logging, command):
    command.ldap_connection = MagicMock()
    command.ldap_connection.search.return_value = True
    command.ldap_connection.response = ['obj1', 'obj2']
    command.objectClass = 'testObject'
    command._get_objects()
    command.ldap_connection.search.assert_called_once_with(
        'dc=ukbonn,dc=de', '(objectclass=testObject)',
        SUBTREE, attributes=['*'])
    mock_logging.info.assert_called_once_with(
        'Found: %s-objects - Count: %i', 'testObject', 2)


@patch('nac.management.commands.export_ldapObjects.logging')
def test_get_objects_not_found(mock_logging, command):
    command.ldap_connection = MagicMock()
    command.ldap_connection.search.return_value = False
    command.ldap_connection.response = []
    command.objectClass = 'testObject'
    command._get_objects()
    command.ldap_connection.search.assert_called_once_with(
        'dc=ukbonn,dc=de', '(objectclass=testObject)',
        SUBTREE, attributes=['*'])
    mock_logging.error.assert_called_once_with(
        'Not Found: %s-objects', 'testObject')


def test_convert_dictlists_to_str(command):
    test_dict = {'key1': ['value1', 'value2'], 'key2': 'value3'}
    result = command._convert_dictlists_to_str(test_dict)
    assert result == {'key1': 'value1,value2', 'key2': 'value3'}


@patch('builtins.open', new_callable=mock_open)
@patch('nac.management.commands.export_ldapObjects.logging')
def test_clear_file(mock_logging, mock_file, command):
    command._clear_file()
    mock_file.assert_called_once_with(CSV_SAVE_FILE, 'w')
    mock_logging.info.assert_called_once_with('Truncating %s', CSV_SAVE_FILE)


@patch('builtins.open', side_effect=Exception('Failed'))
@patch('nac.management.commands.export_ldapObjects.logging')
def test_clear_file_exception(mock_logging, mock_file, command):
    command._clear_file()
    mock_logging.error.assert_called_once_with(
        'Failed to truncate %s -> %s', CSV_SAVE_FILE, 'Failed')


@patch('builtins.open', new_callable=mock_open)
@patch('nac.management.commands.export_ldapObjects.DictWriter')
@patch('nac.management.commands.export_ldapObjects.stat')
@patch('nac.management.commands.export_ldapObjects.logging')
def test_write_object_empty_file(mock_logging, mock_stat,
                                 mock_writer, mock_file, command):
    object_dict = {'attr1': 'value1', 'attr2': ['value2', 'value3']}
    mock_stat.return_value.st_size = 0
    mock_writer_instance = MagicMock()
    mock_writer.return_value = mock_writer_instance
    command.entry_count = 10
    command.write_object(object_dict, 5)
    mock_file.assert_called_once_with(CSV_SAVE_FILE, 'a', newline="")
    mock_writer.assert_called_once_with(
        mock_file(), fieldnames=object_dict.keys(), delimiter=';')
    mock_writer_instance.writeheader.assert_called_once()
    mock_writer_instance.writerows.assert_called_once_with(
        [{'attr1': 'value1', 'attr2': 'value2,value3'}])
    mock_logging.debug.assert_called_once_with(
        'Successfully exported object %i/%i to file: %s ',
        5, 10, CSV_SAVE_FILE)


@patch('builtins.open', new_callable=mock_open)
@patch('nac.management.commands.export_ldapObjects.DictWriter')
@patch('nac.management.commands.export_ldapObjects.stat')
@patch('nac.management.commands.export_ldapObjects.logging')
def test_write_object_non_empty_file(mock_logging, mock_stat,
                                     mock_writer, mock_file, command):
    object_dict = {'attr1': 'value1', 'attr2': ['value2', 'value3']}
    mock_stat.return_value.st_size = 100
    mock_writer_instance = MagicMock()
    mock_writer.return_value = mock_writer_instance
    command.entry_count = 10
    command.write_object(object_dict, 5)
    mock_file.assert_called_once_with(CSV_SAVE_FILE, 'a', newline="")
    mock_writer.assert_called_once_with(
        mock_file(), fieldnames=object_dict.keys(), delimiter=';')
    mock_writer_instance.writeheader.assert_not_called()
    mock_writer_instance.writerows.assert_called_once_with(
        [{'attr1': 'value1', 'attr2': 'value2,value3'}])
    mock_logging.debug.assert_called_once_with(
        'Successfully exported object %i/%i to file: %s ',
        5, 10, CSV_SAVE_FILE)


@patch('builtins.open', side_effect=Exception('Failed'))
@patch('nac.management.commands.export_ldapObjects.logging')
def test_write_object_exception(mock_logging, mock_file, command):
    object_dict = {'attr1': 'value1', 'attr2': ['value2', 'value3']}
    mock_writer_instance = MagicMock()
    command.write_object(object_dict, 5)
    mock_writer_instance.writeheader.assert_not_called()
    mock_writer_instance.writerows.assert_not_called()
    mock_logging.error.assert_called_once_with(
        'Failed to export object to file: %s -> %s', CSV_SAVE_FILE, 'Failed')
