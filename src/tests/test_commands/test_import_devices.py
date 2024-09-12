import pytest
from nac.management.commands.import_devices import Command, \
    DEFAULT_SOURCE_CSV, CSV_SAVE_FILE
from unittest.mock import patch, mock_open, MagicMock
from django.core.exceptions import ValidationError
from nac.models import AuthorizationGroup, DeviceRoleProd, DeviceRoleInst


@pytest.fixture
def command():
    return Command()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "appl_NAC_ForceDot1X, appl_NAC_AllowAccessVPN, appl_NAC_Certificate, "
    "appl_NAC_AllowAccessAIR, appl_NAC_macAddressAIR, appl_NAC_AllowAccessCAB,"
    "appl_NAC_macAddressCAB, expected_result",
    [
        (True, True, "test", True, "001122334455", True, "001122334455", None),
        (True, True, None, True, "001122334455", True, "001122334455",
         ValidationError),
        (True, True, "test", True, None, True, "001122334455",
         ValidationError),
        (True, True, "test", True, "001122334455", True, None,
         ValidationError),
        (False, True, None, True, "001122334455", True, "001122334455",
         ValidationError),
        (True, False, None, True, "001122334455", True, "001122334455",
         ValidationError),
        (False, False, None, True, "001122334455", True, "001122334455", None),
        (True, True, "test", False, None, True, "001122334455", None),
        (True, True, "test", True, "001122334455", False, None, None)
    ]
)
@patch('nac.management.commands.import_devices.transaction.atomic')
@patch('nac.management.commands.import_devices.logging')
def test_check_device(mock_logging, mock_atomic, appl_NAC_ForceDot1X,
                      appl_NAC_AllowAccessVPN,
                      appl_NAC_Certificate, appl_NAC_AllowAccessAIR,
                      appl_NAC_macAddressAIR, appl_NAC_AllowAccessCAB,
                      appl_NAC_macAddressCAB, expected_result, command):

    test_deviceRoleProd = DeviceRoleProd.objects.create(name="test")
    test_deviceRoleInst = DeviceRoleInst.objects.create(name="test")
    test_authorization_group = AuthorizationGroup.objects.create(name="test")
    test_authorization_group.DeviceRoleInst.set([test_deviceRoleInst])
    test_authorization_group.DeviceRoleProd.set([test_deviceRoleProd])
    command.auth_group = 'test'
    data = {
        "name": "test",
        "objectClass": "appl-NAC-Device",
        "authorization_group": test_authorization_group,
        "appl-NAC-DeviceRoleProd": test_deviceRoleProd,
        "appl-NAC-FQDN": "test",
        "appl-NAC-Hostname": "test",
        "appl-NAC-Active": True,
        "appl-NAC-ForceDot1X": appl_NAC_ForceDot1X,
        "appl-NAC-Install": True,
        "appl-NAC-AllowAccessCAB": appl_NAC_AllowAccessCAB,
        "appl-NAC-AllowAccessAIR": appl_NAC_AllowAccessAIR,
        "appl-NAC-AllowAccessVPN": appl_NAC_AllowAccessVPN,
        "appl-NAC-AllowAccessCEL": True,
        "appl-NAC-DeviceRoleInst": test_deviceRoleInst,
        "appl-NAC-macAddressAIR": appl_NAC_macAddressAIR,
        "appl-NAC-macAddressCAB": appl_NAC_macAddressCAB,
        "appl-NAC-Certificate": appl_NAC_Certificate,
        "synchronized": False,
    }

    if expected_result:
        with pytest.raises(expected_result):
            command.check_device(data)
        mock_atomic.assert_called()
    else:
        command.check_device(data)
        mock_logging.debug.assert_called_once_with(
            f"Device {data.get('name')} is valid")


@pytest.mark.django_db
@patch('nac.management.commands.import_devices.transaction.atomic')
@patch('nac.management.commands.import_devices.Command.str_to_bool')
@patch('nac.management.commands.import_devices.logging')
@patch('nac.management.commands.import_devices.DeviceForm')
def test_check_device_exceptions(
        mock_device_form, mock_logging,
        mock_str_to_bool, mock_atomic, command):
    test_deviceRoleProd = DeviceRoleProd.objects.create(name="test")
    test_deviceRoleInst = DeviceRoleInst.objects.create(name="test")
    test_authorization_group = AuthorizationGroup.objects.create(name="test")
    command.auth_group = 'test'
    test_authorization_group.DeviceRoleProd.set([test_deviceRoleProd])
    test_authorization_group.DeviceRoleInst.set([test_deviceRoleInst])
    invalid_device = {
        "name": "test",
        "objectClass": "appl-NAC-Device",
        "authorization_group": test_authorization_group,
        "appl-NAC-DeviceRoleProd": test_deviceRoleProd,
        "appl-NAC-DeviceRoleInst": test_deviceRoleInst}
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
        "name": "test",
        "objectClass": "test_object",
        "authorization_group": test_authorization_group,
        "appl-NAC-DeviceRoleProd": test_deviceRoleProd}
    with pytest.raises(
            Exception, match="Invalid Object-type! EXPECTED: "
                             "appl-NAC-Device <-> ACTUAL: test_object"):
        command.check_device(invalid_device)

    mock_atomic.reset_mock()
    invalid_device = {
        "name": "test",
        "objectClass": "appl-NAC-Device",
        "authorization_group": test_authorization_group,
        "appl-NAC-DeviceRoleProd": "dummy",
        "appl-NAC-DeviceRoleInst": test_deviceRoleInst}
    with pytest.raises(
            Exception,
            match="('DeviceRoleProd: %s not in Database', 'dummy')"):
        command.check_device(invalid_device)
    mock_atomic.assert_called()

    mock_atomic.reset_mock()
    invalid_device = {
        "name": "test",
        "objectClass": "appl-NAC-Device",
        "authorization_group": test_authorization_group,
        "appl-NAC-DeviceRoleProd": test_deviceRoleProd,
        "appl-NAC-DeviceRoleInst": "dummy"}
    with pytest.raises(
            Exception,
            match="('DeviceRoleInst: %s not in Database', 'dummy')"):
        command.check_device(invalid_device)
    mock_atomic.assert_called()

    test_deviceRoleProd = DeviceRoleProd.objects.create(name="dummy")
    test_deviceRoleInst = DeviceRoleInst.objects.create(name="dummy")
    mock_atomic.reset_mock()
    invalid_device = {
        "name": "test",
        "objectClass": "appl-NAC-Device",
        "authorization_group": test_authorization_group,
        "appl-NAC-DeviceRoleProd": "dummy",
        "appl-NAC-DeviceRoleInst": test_deviceRoleInst}
    with pytest.raises(
            Exception, match="DeviceRoleProd: dummy "
            "not in authorization group: test"):
        command.check_device(invalid_device)
    mock_atomic.assert_called()

    test_authorization_group.DeviceRoleProd.set([test_deviceRoleProd])
    mock_atomic.reset_mock()
    invalid_device = {
        "name": "test",
        "objectClass": "appl-NAC-Device",
        "authorization_group": test_authorization_group,
        "appl-NAC-DeviceRoleProd": test_deviceRoleProd,
        "appl-NAC-DeviceRoleInst": "dummy"}
    with pytest.raises(
            Exception, match="DeviceRoleInst: dummy "
            "not in authorization group: test"):
        command.check_device(invalid_device)
    mock_atomic.assert_called()


@pytest.mark.django_db
@patch('nac.management.commands.import_devices.Device.objects.create')
@patch('nac.management.commands.import_devices.logging')
def test_add_device_to_db(mock_logging, mock_create, command):
    device = {"name": "test"}
    mock_create.return_value = None
    assert command.add_device_to_db(device) is True
    mock_create.assert_called()
    mock_logging.info.assert_called()
    mock_logging.debug.assert_called_once_with(
        f"Import device {device['name']} to database: SUCCESSFUL")


@pytest.mark.django_db
@patch('nac.management.commands.import_devices.transaction.atomic')
@patch('nac.management.commands.import_devices.Device.objects.create')
@patch('nac.management.commands.import_devices.logging')
def test_add_device_to_db_exception(mock_logging, mock_create,
                                    mock_atomic, command):
    device = {"name": "test"}
    mock_create.side_effect = Exception("Failed")
    assert command.add_device_to_db(device) is False
    mock_logging.error.assert_called_with(
        "Import device test to database: FAILED")
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
@patch('nac.management.commands.import_devices.DictWriter')
@patch('nac.management.commands.import_devices.stat')
@patch('nac.management.commands.import_devices.logging')
def test_save_invalid_devices_empty_file(mock_logging, mock_stat,
                                         mock_writer, mocked_file, command):
    device = {"name": "test"}
    mock_stat.return_value.st_size = 0
    mock_writer_instance = MagicMock()
    mock_writer.return_value = mock_writer_instance
    command.save_invalid_devices(device)
    mocked_file.assert_called_once_with(CSV_SAVE_FILE,
                                        'a', newline="")
    mock_writer.assert_called_once_with(mocked_file(),
                                        fieldnames=device.keys(),
                                        delimiter=";")
    mock_writer_instance.writeheader.assert_called_once()
    mock_writer_instance.writerows.assert_called_once_with([device])
    mock_logging.info.assert_called_once_with(
        f"Writing invalid device to {CSV_SAVE_FILE}")
    mock_logging.debug.assert_called_once_with(
        f"Writing invalid device to {CSV_SAVE_FILE}: SUCCESSFUL")


@patch('builtins.open', new_callable=mock_open)
@patch('nac.management.commands.import_devices.DictWriter')
@patch('nac.management.commands.import_devices.stat')
def test_save_invalid_devices_non_empty_file(mock_stat, mock_writer,
                                             mock_file, command):
    device = {"name": "test"}
    mock_stat.return_value.st_size = 100
    mock_writer_instance = MagicMock()
    mock_writer.return_value = mock_writer_instance
    command.save_invalid_devices(device)
    mock_writer_instance.writeheader.assert_not_called()


@patch('nac.management.commands.import_devices.logging')
@patch('builtins.open', side_effect=Exception("Failed"))
def test_save_invalid_devices_exception(mock_file, mock_logging, command):
    device = {"name": "test"}
    command.save_invalid_devices(device)
    mock_logging.error.assert_called_once_with(
        f"Writing invalid device to "
        f"{CSV_SAVE_FILE}: FAILED -> Failed")


@patch('builtins.open', new_callable=mock_open, read_data="name\n;test")
@patch('nac.management.commands.import_devices.DictReader')
@patch('nac.management.commands.import_devices.Command.handle_deviceObject')
@patch('nac.management.commands.import_devices.logging')
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
@patch('nac.management.commands.import_devices.DictReader')
@patch('nac.management.commands.import_devices.Command.handle_deviceObject')
@patch('nac.management.commands.import_devices.logging')
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
@patch('nac.management.commands.import_devices.logging')
def test_clear_invalid_devices_file(mock_logging, mock_file, command):
    command.clear_invalid_devices_file()
    mock_file.assert_called_once_with(CSV_SAVE_FILE, "w")
    mock_logging.info.assert_called_once_with(
        f"Removing all entries in {CSV_SAVE_FILE}")


@patch('builtins.open', side_effect=Exception("Failed"))
@patch('nac.management.commands.import_devices.logging')
def test_clear_invalid_devices_file_exception(mock_logging,
                                              mock_file, command):
    command.clear_invalid_devices_file()
    mock_file.assert_called_once_with(CSV_SAVE_FILE, "w")
    mock_logging.error.assert_called_once_with(
        f"Removing all entries in {CSV_SAVE_FILE} FAILED -> Failed"
        )


@pytest.mark.django_db
@patch('nac.management.commands.import_devices.Command.check_device')
@patch('nac.management.commands.import_devices.Command.add_device_to_db')
@patch('nac.management.commands.import_devices.Command.save_invalid_devices')
@patch('nac.management.commands.import_devices.logging')
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
@patch('nac.management.commands.import_devices.Command.check_device')
@patch('nac.management.commands.import_devices.Command.add_device_to_db')
@patch('nac.management.commands.import_devices.Command.save_invalid_devices')
@patch('nac.management.commands.import_devices.logging')
def test_handle_deviceObject_invalid_Device(
        mock_logging, mock_save_invalid_devices,
        mock_add_device_to_db, mock_check_device, command):
    device = {"name": "test"}
    mock_check_device.side_effect = ValidationError("Invalid device")

    command.handle_deviceObject(device)

    mock_check_device.assert_called_once_with(device)
    mock_add_device_to_db.assert_not_called()
    mock_save_invalid_devices.assert_called_once_with(device)
    mock_logging.error.assert_not_called()


@pytest.mark.django_db
@patch('nac.management.commands.import_devices.Command.check_device')
@patch('nac.management.commands.import_devices.Command.add_device_to_db')
@patch('nac.management.commands.import_devices.Command.save_invalid_devices')
@patch('nac.management.commands.import_devices.logging')
def test_handle_deviceObject_exception(
        mock_logging, mock_save_invalid_devices,
        mock_add_device_to_db, mock_check_device, command):
    device = {"name": "test"}
    mock_check_device.side_effect = Exception("Invalid device")

    command.handle_deviceObject(device)

    mock_check_device.assert_called_once_with(device)
    mock_add_device_to_db.assert_not_called()
    mock_save_invalid_devices.assert_not_called()


def test_add_arguments(command):
    mock_parser = MagicMock()
    command.add_arguments(mock_parser)
    mock_parser.add_argument.assert_any_call(
        '-f', '--csv_file',
        default=DEFAULT_SOURCE_CSV,
        help='use a specific csv file [src/ldapObjects.csv]'
    )
    mock_parser.add_argument.assert_any_call(
        '-a', '--auth_group',
        default='DefaultAG',
        help='specify the Device Authorization Group'
    )


@pytest.mark.django_db
@patch('nac.management.commands.import_devices.Command.check_valid_auth_group')
@patch('nac.management.commands.import_devices.setup_console_logger')
@patch('nac.management.commands.import_devices.get_absolute_path')
@patch(
    'nac.management.commands.import_devices.Command.clear_invalid_devices_file')
@patch('nac.management.commands.import_devices.Command.read_csv')
def test_handle(mock_read_csv, mock_clear_invalid_devices_file,
                mock_get_absolute_path, mock_setup_console_logger,
                mock_check_valid_auth_group, command):
    options = {
        'verbosity': 0,
        'csv_file': 'test.csv',
        'auth_group': 'testag'
    }
    mock_get_absolute_path.return_value = 'mockpath/to/test.csv'
    command.handle(**options)
    mock_setup_console_logger.assert_called_once_with(0)
    mock_check_valid_auth_group.assert_called_once_with('testag')
    mock_get_absolute_path.assert_called_once_with('test.csv')
    mock_clear_invalid_devices_file.assert_called_once()
    mock_read_csv.assert_called_once()
    assert command.source_file == 'mockpath/to/test.csv'
    mock_clear_invalid_devices_file.reset_mock()
    mock_check_valid_auth_group.return_value = None
    command.handle(**options)
    mock_clear_invalid_devices_file.assert_not_called()


@pytest.mark.django_db
def test_check_valid_auth_group_exists(command):
    test_authorization_group = AuthorizationGroup.objects.create(name='testag')
    result = command.check_valid_auth_group(test_authorization_group)
    assert result == test_authorization_group


@pytest.mark.django_db
@patch('nac.management.commands.import_devices.logging')
def test_check_valid_auth_group_not_exists(mock_logging, command):
    result = command.check_valid_auth_group('dummy')
    mock_logging.error.assert_called_once_with(
        "Authorization Group-Object: dummy not in Database")
    assert result is None
