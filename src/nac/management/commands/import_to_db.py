from django.core.management.base import BaseCommand
import logging
from os import stat
from csv import DictReader, DictWriter
from django.db import transaction
from nac.models import Device, Area, SecurityGroup
from nac.forms import DeviceForm
from helper.logging import setup_console_logger
from helper.filesystem import get_resources_directory, get_absolute_path
from django.core.exceptions import ValidationError


CSV_SAVE_FILE = "invalid_devices.csv"
DEFAULT_SOURCE_CSV = get_resources_directory() / 'ldap_testobjects.csv'


class Command(BaseCommand):
    help = 'Import devices from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('-f', '--csv_file', default=DEFAULT_SOURCE_CSV, help='use a specific csv file [src/ldap_testobjects.csv]')

    def handle(self, *args, **options):
        setup_console_logger(options['verbosity'])
        self.source_file = get_absolute_path(options['csv_file'])
        self.clear_invalid_devices_file()
        self.read_csv()

    def clear_invalid_devices_file(self):
        try:
            with open(CSV_SAVE_FILE, "w"):
                logging.info(f"Removing all entries in {CSV_SAVE_FILE}")
        except Exception as e:
            logging.error(f"Removing all entries in {CSV_SAVE_FILE} FAILED -> {e}")

    def read_csv(self):
        try:
            with open(self.source_file, "r", newline="") as csvfile:
                logging.info(f"Reading {self.source_file}")
                reader = DictReader(csvfile, delimiter=";")
                for row in reader:
                    self.handle_deviceObject(row)
                    pass
                logging.debug(f"Reading {self.source_file}: SUCCESSFUL")
        except Exception as e:
            logging.error(f"Reading {self.source_file}: FAILED -> {e}")

    def handle_deviceObject(self, deviceObject):
        try:
            device = self.check_device(deviceObject)
            self.add_device_to_db(device)
        except ValidationError:
            self.save_invalid_devices(deviceObject)
        except Exception as e:
            logging.error(f"Handling device object: FAILED -> {e}")

    def check_device(self, deviceObject):
        logging.info(f"Checking validity of device {deviceObject.get('name')}")
        try:
            with transaction.atomic():
                security_group, _ = SecurityGroup.objects.get_or_create(
                    name=deviceObject.get("security_group")
                )
                area, _ = Area.objects.get_or_create(
                    name=deviceObject.get("area")
                )
                area.security_group.add(security_group)
                device_data = {
                    "name": deviceObject.get("name"),
                    "area": area,
                    "security_group": security_group,
                    "appl_NAC_FQDN": deviceObject.get("appl_NAC_FQDN"),
                    "appl_NAC_Hostname": deviceObject.get("appl_NAC_Hostname"),
                    "appl_NAC_Active": self.str_to_bool(deviceObject.get("appl_NAC_Active")),
                    "appl_NAC_ForceDot1X": self.str_to_bool(deviceObject.get("appl_NAC_ForceDot1X")),
                    "appl_NAC_Install": self.str_to_bool(deviceObject.get("appl_NAC_Install")),
                    "appl_NAC_AllowAccessCAB": self.str_to_bool(deviceObject.get("appl_NAC_AllowAccessCAB")),
                    "appl_NAC_AllowAccessAIR": self.str_to_bool(deviceObject.get("appl_NAC_AllowAccessAIR")),
                    "appl_NAC_AllowAccessVPN": self.str_to_bool(deviceObject.get("appl_NAC_AllowAccessVPN")),
                    "appl_NAC_AllowAccessCEL": self.str_to_bool(deviceObject.get("appl_NAC_AllowAccessCEL")),
                    "appl_NAC_DeviceRoleProd": deviceObject.get("appl_NAC_DeviceRoleProd"),
                    "appl_NAC_DeviceRoleInst": deviceObject.get("appl_NAC_DeviceRoleInst"),
                    "appl_NAC_macAddressAIR": deviceObject.get("appl_NAC_macAddressAIR"),
                    "appl_NAC_macAddressCAB": deviceObject.get("appl_NAC_macAddressCAB"),
                    "appl_NAC_Certificate": deviceObject.get("appl_NAC_Certificate"),
                    "synchronized": self.str_to_bool(deviceObject.get("synchronized"))
                }
                device_form = DeviceForm(device_data)
                if device_form.is_valid():
                    logging.debug(f"Device {device_data.get('name')} is valid")
                    return device_data
                else:
                    logging.error(f"Device {device_data.get('name')} is not valid")
                    for field, errors in device_form.errors.items():
                        for reason in errors:
                            logging.error(f"Field: {field} - Error: {reason}")
                    raise ValidationError("Invalid Device")
        except ValidationError:
            raise
        except Exception as e:
            logging.error(f"Checking validity of device {deviceObject.get('name')}: FAILED -> {e}")
            raise

    def str_to_bool(self, input_value):
        return not (input_value in {False, 'False', 'false'})

    def add_device_to_db(self, deviceObject_valid):
        logging.info(f"Import device {deviceObject_valid.get('name')} to database")
        try:
            with transaction.atomic():
                Device.objects.create(**deviceObject_valid)
                logging.debug(f"Import device {deviceObject_valid.get('name')} to database: SUCCESSFUL")
                return True
        except Exception:
            logging.error(f"Import device {deviceObject_valid.get('name')} to database: FAILED")
            return False

    def save_invalid_devices(self, deviceObject_invalid):
        try:
            column_header = deviceObject_invalid.keys()
            with open(CSV_SAVE_FILE, 'a', newline="") as csvfile:
                logging.info(f"Writing invalid device to {CSV_SAVE_FILE}")
                writer = DictWriter(csvfile, fieldnames=column_header, delimiter=";")
                if stat(CSV_SAVE_FILE).st_size == 0:
                    writer.writeheader()
                writer.writerows([deviceObject_invalid])
                logging.debug(f"Writing invalid device to {CSV_SAVE_FILE}: SUCCESSFUL")
        except Exception as e:
            logging.error(f"Writing invalid device to {CSV_SAVE_FILE}: FAILED -> {e}")
