import pytest
from nac.management.commands.import_to_db import Command
from unittest.mock import patch, mock_open, MagicMock
from django.core.exceptions import ValidationError


@pytest.fixture
def command():
    return Command()


@pytest.mark.django_db
@pytest.mark.parametrize("appl_NAC_ForceDot1X, appl_NAC_AllowAccessVPN, appl_NAC_Certificate, appl_NAC_AllowAccessAIR, "
                         "appl_NAC_macAddressAIR, appl_NAC_AllowAccessCAB, appl_NAC_macAddressCAB, expected_result",
                         [(True, True, "test", True, "001122334455", True, "001122334455", None),
                          (True, True, None, True, "001122334455", True, "001122334455", ValidationError),
                          (True, True, "test", True, None, True, "001122334455", ValidationError),
                          (True, True, "test", True, "001122334455", True, None, ValidationError),
                          (False, True, None, True, "001122334455", True, "001122334455", ValidationError),
                          (True, False, None, True, "001122334455", True, "001122334455", ValidationError),
                          (False, False, None, True, "001122334455", True, "001122334455", None),
                          (True, True, "test", False, None, True, "001122334455", None),
                          (True, True, "test", True, "001122334455", False, None, None)])
@patch('nac.management.commands.import_to_db.logging')
def test_check_device(mock_logging, appl_NAC_ForceDot1X, appl_NAC_AllowAccessVPN, appl_NAC_Certificate, appl_NAC_AllowAccessAIR, appl_NAC_macAddressAIR, appl_NAC_AllowAccessCAB, appl_NAC_macAddressCAB, expected_result, command):
    data = {
       "name": "test",
       "area": "test_area",
       "security_group": "test_sec_group",
       "appl_NAC_FQDN": "test",
       "appl_NAC_Hostname": "test",
       "appl_NAC_Active": True,
       "appl_NAC_ForceDot1X": appl_NAC_ForceDot1X,
       "appl_NAC_Install": True,
       "appl_NAC_AllowAccessCAB": appl_NAC_AllowAccessCAB,
       "appl_NAC_AllowAccessAIR": appl_NAC_AllowAccessAIR,
       "appl_NAC_AllowAccessVPN": appl_NAC_AllowAccessVPN,
       "appl_NAC_AllowAccessCEL": True,
       "appl_NAC_DeviceRoleProd": "test",
       "appl_NAC_DeviceRoleInst": "test",
       "appl_NAC_macAddressAIR": appl_NAC_macAddressAIR,
       "appl_NAC_macAddressCAB": appl_NAC_macAddressCAB,
       "appl_NAC_Certificate": appl_NAC_Certificate,
       "synchronized": False,
    }
    if expected_result:
        with pytest.raises(expected_result):
            command.check_device(data)
    else:
        command.check_device(data)
        mock_logging.debug.assert_called_once_with(f"Device {data.get('name')} is valid")


@pytest.mark.django_db
@patch('nac.management.commands.import_to_db.Device.objects.create')
@patch('nac.management.commands.import_to_db.logging')
def test_add_device_to_db(mock_logging, mock_create, command):
    device = {"name": "test"}
    mock_create.return_value = None
    assert command.add_device_to_db(device) is True
    mock_create.assert_called()
    mock_logging.debug.assert_called()
    mock_logging.debug.assert_called_once_with(f"Import device {device['name']} to database: SUCCESSFUL")


@pytest.mark.django_db
@patch('nac.management.commands.import_to_db.Device.objects.create')
@patch('nac.management.commands.import_to_db.logging')
def test_add_device_to_db_exception(mock_logging, mock_create, command):
    device = {"name": "test"}
    mock_create.side_effect = Exception("Failed")
    assert command.add_device_to_db(device) is False
    mock_create.assert_called()
    mock_logging.error.assert_called()


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


@pytest.mark.django_db
@patch('nac.management.commands.import_to_db.Command.check_device')
@patch('nac.management.commands.import_to_db.Command.add_device_to_db')
@patch('nac.management.commands.import_to_db.Command.save_invalid_devices')
def test_handle_object_valid_device(mock_save_invalid_devices, mock_add_device_to_db, mock_check_device, command):
    device = {"name": "test"}
    mock_check_device.return_value = (device)
    command.handle_deviceObject(device)
    mock_add_device_to_db.assert_called()
    mock_save_invalid_devices.assert_not_called()


@pytest.mark.django_db
@patch('nac.management.commands.import_to_db.Command.check_device')
@patch('nac.management.commands.import_to_db.Command.add_device_to_db')
@patch('nac.management.commands.import_to_db.Command.save_invalid_devices')
def test_handle_object_invalid_device(mock_save_invalid_devices, mock_add_device_to_db, mock_check_device, command):
    device = {"name": "test"}
    command.check_device = MagicMock(side_effect=ValidationError("Invalid device"))
    command.handle_deviceObject(device)
    mock_add_device_to_db.assert_not_called()
    mock_save_invalid_devices.assert_called_with(device)


def test_save_invalid_devices_empty_file(command):
    device = {"name": "test"}
    with patch('builtins.open', mock_open()) as mocked_file, \
         patch('nac.management.commands.import_to_db.DictWriter') as mock_writer, \
         patch('nac.management.commands.import_to_db.stat') as mock_stat, \
         patch('nac.management.commands.import_to_db.logging') as mock_logging:
        mock_stat.return_value.st_size = 0
        mock_writer_instance = MagicMock()
        mock_writer.return_value = mock_writer_instance
        command.save_invalid_devices(device)
        mocked_file.assert_called_once_with(command.CSV_SAVE_FILE, 'a', newline="")
        mock_writer.assert_called_once_with(mocked_file(), fieldnames=device.keys(), delimiter=";")
        mock_writer_instance.writeheader.assert_called_once()
        mock_writer_instance.writerows.assert_called_once_with([device])
        mock_logging.info.assert_called_once_with(f"Writing invalid device to {command.CSV_SAVE_FILE}")
        mock_logging.debug.assert_called_once_with(f"Writing invalid device to {command.CSV_SAVE_FILE}: SUCCESSFUL")


def test_save_invalid_devices_non_empty_file(command):
    device = {"name": "test"}
    with patch('nac.management.commands.import_to_db.DictWriter') as mock_writer, \
         patch('nac.management.commands.import_to_db.stat') as mock_stat:
        mock_stat.return_value.st_size = 100
        mock_writer_instance = MagicMock()
        mock_writer.return_value = mock_writer_instance
        command.save_invalid_devices(device)
        mock_writer_instance.writeheader.assert_not_called()


def test_save_invalid_devices_exception(command):
    device = {"name": "test"}
    with patch('builtins.open', side_effect=Exception("Failed")), \
         patch('nac.management.commands.import_to_db.logging') as mock_logging:
        command.save_invalid_devices(device)
        mock_logging.error.assert_called_once_with(f"Writing invalid device to {command.CSV_SAVE_FILE}: FAILED -> Failed")


def test_read_csv(command):
    command.source_file = "test.csv"
    with patch('builtins.open', mock_open(read_data="name\n;test")) as mock_file, \
         patch('nac.management.commands.import_to_db.DictReader') as mock_reader, \
         patch('nac.management.commands.import_to_db.Command.handle_deviceObject') as mock_handler, \
         patch('nac.management.commands.import_to_db.logging') as mock_logging:
        mock_reader.return_value = [{"name": "test"}]
        mock_handler.return_value = None
        command.read_csv()
        mock_file.assert_called_once_with("test.csv", "r", newline="")
        mock_reader.assert_called_once_with(mock_file(), delimiter=";")
        mock_handler.assert_called_once_with({"name": "test"})
        mock_logging.info.assert_called_once_with("Reading test.csv")
        mock_logging.debug.assert_called_once_with("Reading test.csv: SUCCESSFUL")


def test_clear_invalid_devices_file(command):
    with patch("builtins.open", mock_open()) as mock_file, \
         patch('nac.management.commands.import_to_db.logging') as mock_logging:
        command.clear_invalid_devices_file()
    mock_file.assert_called_once_with(command.CSV_SAVE_FILE, "w")
    mock_logging.info.assert_called_once_with(f"Removing all entries in {command.CSV_SAVE_FILE}")


def test_clear_invalid_devices_file_exception(command):
    with patch("builtins.open", side_effect=Exception("Failed")) as mock_file, \
         patch('nac.management.commands.import_to_db.logging') as mock_logging:
        command.clear_invalid_devices_file()
    mock_file.assert_called_once_with(command.CSV_SAVE_FILE, "w")
    mock_logging.error.assert_called_once_with(f"Removing all entries in {command.CSV_SAVE_FILE} FAILED -> Failed")
