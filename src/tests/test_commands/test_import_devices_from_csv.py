import pytest
from nac.management.commands.import_devices_from_csv import Command, \
    DEFAULT_SOURCE_FILE, DEFAULT_SAVE_FILE, DEFAULT_OU_MAPPING, DEFAULT_CSV_MAPPING
from unittest.mock import patch, mock_open, MagicMock
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.management.base import CommandError
from nac.models import AdministrationGroup, DeviceRoleProd, DeviceRoleInst, Device, DNSDomain
from helper.database import MacList
from helper.config import get_config_from_json


@pytest.fixture
def command():
    return Command()


@pytest.mark.django_db
@pytest.mark.parametrize("appl_NAC_ForceDot1X, appl_NAC_AllowAccessVPN, appl_NAC_Certificate, appl_NAC_AllowAccessAIR, "
                         "appl_NAC_macAddressAIR, appl_NAC_AllowAccessCAB, appl_NAC_macAddressCAB, test_hostname, expected_result",
                         [(True, True, "test", True, "001132334455", True, "001132334455", "device_1", None),
                          (True, True, None, True, "001142334455", True, "001142334455", "device_1", None),
                          (True, True, "test", True, None, True, "001152334455", "device_1", ValidationError),
                          (True, True, "test", True, "001162334455", True, None, "device_1", ValidationError),
                          (False, False, None, True, "001192334455", True, "001192334455", "device_1", None),
                          (True, True, "test", False, None, True, "001123334455", "device_1", None),
                          (True, True, "test", False, None, True, "001123334455", "device.1", ValidationError),
                          (True, True, "test", True, "001122434455", False, None, "device_1", None)])
@patch('nac.management.commands.import_devices_from_csv.transaction.atomic')
@patch('nac.management.commands.import_devices_from_csv.logging')
@patch('helper.database.MacList.check_existing_mac')
def test_check_device(mock_check_existing_mac, mock_logging, mock_atomic, appl_NAC_ForceDot1X,
                      appl_NAC_AllowAccessVPN,
                      appl_NAC_Certificate, appl_NAC_AllowAccessAIR,
                      appl_NAC_macAddressAIR, appl_NAC_AllowAccessCAB,
                      appl_NAC_macAddressCAB, test_hostname, expected_result, command):

    test_DeviceRoleProd = DeviceRoleProd.objects.create(name="test")
    test_DeviceRoleInst = DeviceRoleInst.objects.create(name="test2")
    test_domain = DNSDomain.objects.create(name="test.com")
    test_administration_group = AdministrationGroup.objects.create(name="test")
    test_administration_group.DeviceRoleProd.set([test_DeviceRoleProd])
    test_administration_group.DeviceRoleInst.set([test_DeviceRoleInst])
    command.admin_group = 'test'
    command.update = False
    command.csv_mapping = get_config_from_json(DEFAULT_CSV_MAPPING)
    command.csv_mapping['DeviceRoleCriteria']['MAPPING'] = False
    command.ou_mapping = {}
    command.mac_list = MacList()
    data = {
        "objectClass": "appl-NAC-Device",
        "asset_id": "None",
        "vlan": 100,
        "dns_domain": test_domain,
        "appl-NAC-Hostname": test_hostname,
        "administration_group": test_administration_group,
        "appl-NAC-DeviceRoleProd": test_DeviceRoleProd,
        "appl-NAC-Active": True,
        "appl-NAC-ForceDot1X": appl_NAC_ForceDot1X,
        "appl-NAC-Install": True,
        "appl-NAC-AllowAccessCAB": appl_NAC_AllowAccessCAB,
        "appl-NAC-AllowAccessAIR": appl_NAC_AllowAccessAIR,
        "appl-NAC-AllowAccessVPN": appl_NAC_AllowAccessVPN,
        "appl-NAC-AllowAccessCEL": True,
        "appl-NAC-DeviceRoleInst": test_DeviceRoleInst,
        "appl-NAC-macAddressAIR": appl_NAC_macAddressAIR,
        "appl-NAC-macAddressCAB": appl_NAC_macAddressCAB,
        "appl-NAC-Certificate": appl_NAC_Certificate,
        "synchronized": False,
        "additional_info": "Placeholder"
    }

    if expected_result:
        with pytest.raises(expected_result):
            command.check_device(data)
        mock_atomic.assert_called()
    else:
        mock_check_existing_mac.return_value = False, None
        result = command.check_device(data)
        assert type(result) is dict
        mock_logging.debug.assert_any_call(
            f"Device {data.get('appl-NAC-Hostname')} is valid")


@pytest.mark.django_db
@patch('nac.models.Device.objects.filter')
@patch('nac.management.commands.import_devices_from_csv.transaction.atomic')
@patch('nac.management.commands.import_devices_from_csv.Command.str_to_bool')
@patch('nac.management.commands.import_devices_from_csv.logging')
@patch('nac.management.commands.import_devices_from_csv.DeviceForm')
@patch('helper.database.MacList.check_existing_mac')
def test_check_device_exceptions(
        mock_check_existing_mac,
        mock_device_form, mock_logging,
        mock_str_to_bool, mock_atomic, mock_device_filter, command):
    test_deviceRoleProd = DeviceRoleProd.objects.create(name="test")
    test_deviceRoleInst = DeviceRoleInst.objects.create(name="test")
    test_administration_group = AdministrationGroup.objects.create(name="test")
    command.admin_group = 'test'
    command.csv_mapping = get_config_from_json(DEFAULT_CSV_MAPPING)
    command.csv_mapping['DeviceRoleCriteria']['MAPPING'] = False
    command.ou_mapping = {}
    command.mac_list = MacList()
    test_administration_group.DeviceRoleProd.set([test_deviceRoleProd])
    test_administration_group.DeviceRoleInst.set([test_deviceRoleInst])
    invalid_device = {
        "objectClass": "appl-NAC-Device",
        "administration_group": test_administration_group,
        "appl-NAC-DeviceRoleProd": test_deviceRoleProd,
        "appl-NAC-DeviceRoleInst": test_deviceRoleInst,
        "appl-NAC-Hostname": "test"
        }
    mock_form = MagicMock()
    mock_form.is_valid.return_value = False
    mock_form.errors = {"Type": ["Reason"]}
    mock_device_form.return_value = mock_form

    with pytest.raises(ValidationError, match="Invalid Device"):
        command.check_device(invalid_device)
    mock_logging.error.assert_called_with("Field: Type - Error: Reason")
    assert mock_logging.error.call_count == 2  # Invalid-Error, Error Data
    mock_atomic.assert_called()

    mock_atomic.reset_mock()

    mock_str_to_bool.side_effect = Exception("Failed")
    with pytest.raises(Exception, match="Failed"):
        command.check_device(invalid_device)
    mock_logging.error.assert_called_with(
        "Checking validity of device test: FAILED -> Failed"
    )
    mock_atomic.assert_called()

    mock_atomic.reset_mock()
    invalid_device = {
        "objectClass": "test_object",
        "administration_group": test_administration_group,
        "appl-NAC-DeviceRoleProd": test_deviceRoleProd}
    with pytest.raises(
            Exception, match="Invalid Object-type! EXPECTED: "
                             "appl-NAC-Device <-> ACTUAL: test_object"):
        command.check_device(invalid_device)

    mock_atomic.reset_mock()
    invalid_device = {
        "objectClass": "appl-NAC-Device",
        "administration_group": test_administration_group,
        "appl-NAC-DeviceRoleProd": "dummy",
        "appl-NAC-DeviceRoleInst": test_deviceRoleInst}
    with pytest.raises(
            ValidationError,
            match="('DeviceRoleProd: dummy not in Database')"):
        command.check_device(invalid_device)
    mock_atomic.assert_called()

    mock_atomic.reset_mock()
    invalid_device = {
        "objectClass": "appl-NAC-Device",
        "administration_group": test_administration_group,
        "appl-NAC-DeviceRoleProd": test_deviceRoleProd,
        "appl-NAC-DeviceRoleInst": "dummy"}
    with pytest.raises(
            ValidationError,
            match="('DeviceRoleInst: dummy not in Database')"):
        command.check_device(invalid_device)
    mock_atomic.assert_called()

    test_deviceRoleProd = DeviceRoleProd.objects.create(name="dummy")
    test_deviceRoleInst = DeviceRoleInst.objects.create(name="dummy")
    mock_atomic.reset_mock()
    invalid_device = {
        "objectClass": "appl-NAC-Device",
        "administration_group": test_administration_group,
        "appl-NAC-DeviceRoleProd": "dummy",
        "appl-NAC-DeviceRoleInst": test_deviceRoleInst}
    with pytest.raises(
            ValidationError, match="DeviceRoleProd: dummy "
            "not in administration group: test"):
        command.check_device(invalid_device)
    mock_atomic.assert_called()

    test_administration_group.DeviceRoleProd.set([test_deviceRoleProd])
    mock_atomic.reset_mock()
    invalid_device = {
        "objectClass": "appl-NAC-Device",
        "administration_group": test_administration_group,
        "appl-NAC-DeviceRoleProd": test_deviceRoleProd,
        "appl-NAC-DeviceRoleInst": "dummy"}
    with pytest.raises(
            ValidationError, match="DeviceRoleInst: dummy "
            "not in administration group: test"):
        command.check_device(invalid_device)
    mock_atomic.assert_called()

    test_administration_group.DeviceRoleProd.set([test_deviceRoleProd])
    test_administration_group.DeviceRoleInst.set([test_deviceRoleInst])
    Device.objects.create(appl_NAC_Hostname="host")
    command.update = False
    mock_form = MagicMock()
    mock_form.is_valid.return_value = True
    command.str_to_bool = MagicMock(return_value=False)
    mock_device_form.return_value = mock_form
    valid_device = {
        "objectClass": "appl-NAC-Device",
        "appl-NAC-Hostname": "host",
        "administration_group": test_administration_group,
        "appl-NAC-DeviceRoleProd": test_deviceRoleProd,
        "appl-NAC-DeviceRoleInst": test_deviceRoleInst}
    mock_check_existing_mac.return_value = True, 0
    with pytest.raises(ValidationError,
                       match="Device host exists and will not get updated"):
        command.check_device(valid_device)
    mock_atomic.assert_called()

    command.update = True
    command.check_device(valid_device)
    mock_logging.debug.assert_any_call(
        "Updating Device host"
    )
    mock_device_filter.return_value.update.assert_called_once()


@pytest.mark.django_db
@patch('nac.management.commands.import_devices_from_csv.Device.objects.create')
@patch('nac.management.commands.import_devices_from_csv.logging')
@patch('helper.database.MacList.update_mac_list')
def test_add_device_to_db_success(mock_update_mac_list, mock_logging, mock_create, command):
    device = {
        "name": "test_device",
        "id": 1,
    }
    command.mac_list = MacList()
    mock_create.return_value = MagicMock(spec=['__dict__'])
    mock_create.return_value.__dict__ = device

    result = command.add_device_to_db(device)

    assert result is True
    mock_create.assert_called_once_with(**device)
    mock_update_mac_list.assert_called_once_with(device)
    mock_logging.info.assert_called_once_with(f"Import device {device['name']} to database")
    mock_logging.debug.assert_called_once_with(f"Import device {device['name']} to database: SUCCESSFUL")


@pytest.mark.django_db
@patch('nac.management.commands.import_devices_from_csv.transaction.atomic')
@patch('nac.management.commands.import_devices_from_csv.Device.objects.create')
@patch('nac.management.commands.import_devices_from_csv.logging')
def test_add_device_to_db_exception(mock_logging, mock_create,
                                    mock_atomic, command):
    device = {"name": "test"}
    mock_create.side_effect = Exception("Failed")
    assert command.add_device_to_db(device) is False
    mock_logging.error.assert_called_with(
        "Import device test to database: FAILED -> Failed")
    mock_atomic.assert_called_once()


@pytest.mark.parametrize("input_value, expected_output", [
    (False, False),
    ('False', False),
    ('false', False),
    (True, True),
    ('True', True),
    ('true', True),
    ('', True),
    ('anything', True),
    (None, True),
    (0, False),
    (1, True),
])
def test_str_to_bool(input_value, expected_output, command):
    assert command.str_to_bool(input_value) == expected_output


@patch('builtins.open', new_callable=mock_open)
@patch('nac.management.commands.import_devices_from_csv.DictWriter')
@patch('nac.management.commands.import_devices_from_csv.stat')
@patch('nac.management.commands.import_devices_from_csv.logging')
def test_save_invalid_devices_empty_file(mock_logging, mock_stat,
                                         mock_writer, mocked_file, command):
    device = {"name": "test"}
    mock_stat.return_value.st_size = 0
    mock_writer_instance = MagicMock()
    mock_writer.return_value = mock_writer_instance
    command.save_invalid_devices(device)
    mocked_file.assert_called_once_with(DEFAULT_SAVE_FILE,
                                        'a', newline="")
    mock_writer.assert_called_once_with(mocked_file(),
                                        fieldnames=device.keys(),
                                        delimiter=";")
    mock_writer_instance.writeheader.assert_called_once()
    mock_writer_instance.writerows.assert_called_once_with([device])
    mock_logging.info.assert_called_once_with(
        f"Writing invalid device to {DEFAULT_SAVE_FILE}")
    mock_logging.debug.assert_called_once_with(
        f"Writing invalid device to {DEFAULT_SAVE_FILE}: SUCCESSFUL")


@patch('builtins.open', new_callable=mock_open)
@patch('nac.management.commands.import_devices_from_csv.DictWriter')
@patch('nac.management.commands.import_devices_from_csv.stat')
def test_save_invalid_devices_non_empty_file(mock_stat, mock_writer,
                                             mock_file, command):
    device = {"name": "test"}
    mock_stat.return_value.st_size = 100
    mock_writer_instance = MagicMock()
    mock_writer.return_value = mock_writer_instance
    command.save_invalid_devices(device)
    mock_writer_instance.writeheader.assert_not_called()


@patch('nac.management.commands.import_devices_from_csv.logging')
@patch('builtins.open', side_effect=Exception("Failed"))
def test_save_invalid_devices_exception(mock_file, mock_logging, command):
    device = {"name": "test"}
    command.save_invalid_devices(device)
    mock_logging.error.assert_called_once_with(
        f"Writing invalid device to "
        f"{DEFAULT_SAVE_FILE}: FAILED -> Failed")


@patch('builtins.open', new_callable=mock_open, read_data="name\n;test")
@patch('nac.management.commands.import_devices_from_csv.DictReader')
@patch('nac.management.commands.import_devices_from_csv.Command.handle_deviceObject')
@patch('nac.management.commands.import_devices_from_csv.logging')
def test_read_csv(mock_logging, mock_handler, mock_reader, mock_file, command):
    command.source_file = "test.csv"
    mock_reader.return_value = [{"name": "test"}]
    mock_handler.return_value = None
    command.read_csv()
    mock_file.assert_called_once_with("test.csv", "r", newline="")
    mock_reader.assert_called_once_with(mock_file(), delimiter=";")
    mock_handler.assert_called_once_with({"name": "test"})
    mock_logging.info.assert_called_once_with("Reading test.csv")
    mock_logging.debug.assert_called_once_with(
        "Reading test.csv: SUCCESSFUL")


@patch('builtins.open', side_effect=Exception("Failed"))
@patch('nac.management.commands.import_devices_from_csv.DictReader')
@patch('nac.management.commands.import_devices_from_csv.Command.handle_deviceObject')
@patch('nac.management.commands.import_devices_from_csv.logging')
def test_read_csv_exception(mock_logging, mock_handler,
                            mock_reader, mock_file, command):
    command.source_file = "test.csv"
    command.read_csv()
    mock_file.assert_called_once_with("test.csv", "r", newline="")
    mock_reader.assert_not_called()
    mock_handler.assert_not_called()
    mock_logging.error.assert_called_once_with(
        "Reading test.csv: FAILED -> Failed")


@patch('builtins.open', new_callable=mock_open)
@patch('nac.management.commands.import_devices_from_csv.logging')
def test_clear_invalid_devices_file(mock_logging, mock_file, command):
    command.clear_invalid_devices_file()
    mock_file.assert_called_once_with(DEFAULT_SAVE_FILE, "w")
    mock_logging.info.assert_called_once_with(
        f"Removing all entries in {DEFAULT_SAVE_FILE}")


@patch('builtins.open', side_effect=Exception("Failed"))
@patch('nac.management.commands.import_devices_from_csv.logging')
def test_clear_invalid_devices_file_exception(mock_logging,
                                              mock_file, command):
    command.clear_invalid_devices_file()
    mock_file.assert_called_once_with(DEFAULT_SAVE_FILE, "w")
    mock_logging.error.assert_called_once_with(
        f"Removing all entries in {DEFAULT_SAVE_FILE} FAILED -> Failed"
        )


@pytest.mark.django_db
@patch('nac.management.commands.import_devices_from_csv.Command.check_device')
@patch('nac.management.commands.import_devices_from_csv.Command.add_device_to_db')
@patch('nac.management.commands.import_devices_from_csv.Command.save_invalid_devices')
@patch('nac.management.commands.import_devices_from_csv.logging')
def test_handle_deviceObject(
        mock_logging, mock_save_invalid_devices,
        mock_add_device_to_db, mock_check_device, command):
    device = {"name": "test"}
    mock_check_device.return_value = device
    mock_add_device_to_db.return_value = True

    command.handle_deviceObject(device)

    mock_check_device.assert_called_once_with(device)
    mock_add_device_to_db.assert_called_once_with(device)
    mock_save_invalid_devices.assert_not_called()
    mock_logging.error.assert_not_called()


@pytest.mark.django_db
@patch('nac.management.commands.import_devices_from_csv.Command.check_device')
@patch('nac.management.commands.import_devices_from_csv.Command.add_device_to_db')
@patch('nac.management.commands.import_devices_from_csv.Command.save_invalid_devices')
@patch('nac.management.commands.import_devices_from_csv.logging')
def test_handle_deviceObject_invalid_Device(
        mock_logging, mock_save_invalid_devices,
        mock_add_device_to_db, mock_check_device, command):
    device = {"name": "test"}
    mock_check_device.side_effect = ValidationError("Invalid device")

    command.handle_deviceObject(device)

    mock_check_device.assert_called_once_with(device)
    mock_add_device_to_db.assert_not_called()
    mock_save_invalid_devices.assert_called_once_with(device)
    mock_logging.error.assert_called_once_with("Invalid Device -> ['Invalid device']")


@pytest.mark.django_db
@patch('nac.management.commands.import_devices_from_csv.Command.check_device')
@patch('nac.management.commands.import_devices_from_csv.Command.add_device_to_db')
@patch('nac.management.commands.import_devices_from_csv.Command.save_invalid_devices')
@patch('nac.management.commands.import_devices_from_csv.logging')
def test_handle_deviceObject_exception(
        mock_logging, mock_save_invalid_devices,
        mock_add_device_to_db, mock_check_device, command):
    device = {"name": "test"}
    mock_check_device.side_effect = Exception("Invalid device")

    command.handle_deviceObject(device)
    mock_logging.error.assert_called_once_with("Error: Handling device Object failed -> Invalid device")
    mock_check_device.assert_called_once_with(device)
    mock_add_device_to_db.assert_not_called()
    mock_save_invalid_devices.assert_not_called()


def test_add_arguments(command):
    mock_parser = MagicMock()
    command.add_arguments(mock_parser)
    mock_parser.add_argument.assert_any_call(
        '-f', '--csv_file',
        default=DEFAULT_SOURCE_FILE,
        help='use a specific csv file [src/ldapObjects.csv]'
    )
    mock_parser.add_argument.assert_any_call(
        '-a', '--admin_group',
        default='AdminGroupDefault',
        help='specify the Device Administration Group'
    )
    mock_parser.add_argument.assert_any_call(
        '-u', '--update',
        action='store_true',
        help='specify if existing Devices should be updated'
    )


@pytest.mark.django_db
@patch('nac.management.commands.import_devices_from_csv.Command.check_valid_admin_group')
@patch('nac.management.commands.import_devices_from_csv.setup_console_logger')
@patch('nac.management.commands.import_devices_from_csv.get_existing_path')
@patch(
    'nac.management.commands.import_devices_from_csv.Command.clear_invalid_devices_file')
@patch('nac.management.commands.import_devices_from_csv.Command.read_csv')
def test_handle(mock_read_csv, mock_clear_invalid_devices_file,
                mock_get_existing_path, mock_setup_console_logger,
                mock_check_valid_admin_group, command):
    options = {
        'verbosity': 0,
        'csv_file': 'test.csv',
        'admin_group': 'testag',
        'update': False,
        'csv_config': DEFAULT_CSV_MAPPING,
        'ou_config': DEFAULT_OU_MAPPING
    }
    mock_get_existing_path.return_value = 'mockpath/to/test.csv'
    command.handle(**options)
    mock_setup_console_logger.assert_called_once_with(0)
    mock_check_valid_admin_group.assert_called_once_with('testag')
    mock_get_existing_path.assert_called_once_with('test.csv')
    mock_clear_invalid_devices_file.assert_called_once()
    mock_read_csv.assert_called_once()
    assert command.source_file == 'mockpath/to/test.csv'

    mock_clear_invalid_devices_file.reset_mock()
    mock_check_valid_admin_group.return_value = None
    with pytest.raises(CommandError,
                       match="Invalid admin group 'testag'."):
        command.handle(**options)
    mock_clear_invalid_devices_file.assert_not_called()

    mock_clear_invalid_devices_file.reset_mock()
    mock_get_existing_path.return_value = None
    with pytest.raises(CommandError,
                       match="The path 'test.csv' does not exist."):
        command.handle(**options)
    mock_clear_invalid_devices_file.assert_not_called()


@pytest.mark.django_db
def test_check_valid_admin_group_exists(command):
    test_administration_group = AdministrationGroup.objects.create(name='testag')
    result = command.check_valid_admin_group(test_administration_group)
    assert result == test_administration_group


@pytest.mark.django_db
@patch('nac.management.commands.import_devices_from_csv.logging')
def test_check_valid_admin_group_not_exists(mock_logging, command):
    result = command.check_valid_admin_group('dummy')
    mock_logging.error.assert_called_once_with(
        "Administration Group-Object: dummy not in Database")
    assert result is None


def test_get_set_or_default(command):

    assert command.get_set_or_default({'SET': 'value', 'DEFAULT': 'default'}) == 'value'
    assert command.get_set_or_default({'SET': None, 'DEFAULT': 'default'}) == 'default'

    with pytest.raises(KeyError):
        command.get_set_or_default({'DEFAULT': 'default'})


def test_get_deviceRole_ou_mapping(command):
    command.csv_mapping = {
        "DeviceRoleCriteria": {
            "DEFAULT": "OU",
            "SET": None,
            "MAPPING": True
        }
    }
    command.ou_mapping = {
        "DEFAULT": {
            "DeviceRoleProd": "DeviceRoleProdDefault",
            "DeviceRoleInst": "DeviceRoleInstDefault"
        },
        "OU": {
            "DeviceRoleProd": "DeviceRoleProd",
            "DeviceRoleInst": "DeviceRoleInst"
        }
    }
    device_object = {'OU': 'OU'}
    mock_deviceroleprod = MagicMock()
    mock_deviceroleinst = MagicMock()

    with patch('nac.models.DeviceRoleProd.objects.get', return_value=mock_deviceroleprod) as mock_prod_get, \
            patch('nac.models.DeviceRoleInst.objects.get', return_value=mock_deviceroleinst) as mock_inst_get:

        result = command.get_deviceRole(device_object)

        mock_prod_get.assert_called_once_with(name='DeviceRoleProd')
        mock_inst_get.assert_called_once_with(name='DeviceRoleInst')
        assert result == (mock_deviceroleprod, mock_deviceroleinst)

    device_object = {'OU': '404'}
    mock_deviceroleprod = MagicMock()
    mock_deviceroleinst = MagicMock()

    with patch('nac.models.DeviceRoleProd.objects.get', return_value=mock_deviceroleprod) as mock_prod_get, \
            patch('nac.models.DeviceRoleInst.objects.get', return_value=mock_deviceroleinst) as mock_inst_get:

        result = command.get_deviceRole(device_object)

        mock_prod_get.assert_called_once_with(name='DeviceRoleProdDefault')
        mock_inst_get.assert_called_once_with(name='DeviceRoleInstDefault')
        assert result == (mock_deviceroleprod, mock_deviceroleinst)


def test_get_deviceRole_csv_mapping(command):
    command.csv_mapping = {
        "DeviceRoleCriteria": {
            "MAPPING": False
        },
        "appl-NAC-DeviceRoleProd": {
            "DEFAULT": "appl-NAC-DeviceRoleProd",
            "SET": None
        },
        "appl-NAC-DeviceRoleInst": {
            "DEFAULT": "appl-NAC-DeviceRoleInst",
            "SET": None
        }
    }
    device_object = {'appl-NAC-DeviceRoleProd': 'DeviceRoleProd1', 'appl-NAC-DeviceRoleInst': 'DeviceRoleInst1'}
    mock_deviceroleprod = MagicMock()
    mock_deviceroleinst = MagicMock()

    with patch('nac.models.DeviceRoleProd.objects.get', return_value=mock_deviceroleprod) as mock_prod_get, \
            patch('nac.models.DeviceRoleInst.objects.get', return_value=mock_deviceroleinst) as mock_inst_get:

        result = command.get_deviceRole(device_object)

        mock_prod_get.assert_called_once_with(name='DeviceRoleProd1')
        mock_inst_get.assert_called_once_with(name='DeviceRoleInst1')
        assert result == (mock_deviceroleprod, mock_deviceroleinst)


def test_get_deviceRole_ou_mapping_validation_errors(command):
    command.csv_mapping = {
        "DeviceRoleCriteria": {
            "DEFAULT": "OU",
            "SET": None,
            "MAPPING": True
        }
    }
    command.ou_mapping = {
        "OU": {
            "DeviceRoleProd": "DeviceRoleProd1",
            "DeviceRoleInst": "DeviceRoleInst1"
        }
    }
    device_object = {'OU': 'OU'}

    with patch('nac.models.DeviceRoleProd.objects.get', side_effect=ObjectDoesNotExist()), \
            pytest.raises(ValidationError) as excinfo:
        command.get_deviceRole(device_object)

    assert "DeviceRoleProd: DeviceRoleProd1 not in Database" in str(excinfo.value)

    with patch('nac.models.DeviceRoleProd.objects.get', return_value=MagicMock()), \
            patch('nac.models.DeviceRoleInst.objects.get', side_effect=ObjectDoesNotExist()), \
            pytest.raises(ValidationError) as excinfo:
        command.get_deviceRole(device_object)

    assert "DeviceRoleInst: DeviceRoleInst1 not in Database" in str(excinfo.value)
