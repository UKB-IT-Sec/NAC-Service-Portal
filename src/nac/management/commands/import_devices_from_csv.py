import logging
from os import stat
from csv import DictReader, DictWriter
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from nac.models import Device, AuthorizationGroup, DeviceRoleProd, DeviceRoleInst
from nac.forms import DeviceForm
from helper.logging import setup_console_logger
from helper.filesystem import get_resources_directory, get_existing_path

DEFAULT_SOURCE_FILE = get_resources_directory() / 'ldapObjects.csv'
SAVE_FILE = get_resources_directory() / "invalid_devices.csv"


class Command(BaseCommand):

    help = 'Import devices from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '-f', '--csv_file',
            default=DEFAULT_SOURCE_FILE,
            help='use a specific csv file [src/ldapObjects.csv]'
        )
        parser.add_argument(
            '-a', '--auth_group',
            default='DefaultAG',
            help='specify the Device Authorization Group'
        )
        parser.add_argument(
            '-u', '--update',
            action='store_true',
            help='specify if existing Devices should be updated'
        )

    def handle(self, *args, **options):
        setup_console_logger(options['verbosity'])
        self.source_file = get_existing_path(options['csv_file'])
        self.update = options['update']
        if not self.source_file:
            logging.error(
                f"The path '{options['csv_file']}'does not exist.")
            raise CommandError(
                f"The path '{options['csv_file']}' does not exist.")
        self.auth_group = self.check_valid_auth_group(options['auth_group'])
        if not self.auth_group:
            logging.error(
                f"Invalid auth group '{options['auth_group']}'.")
            raise CommandError(
                f"Invalid auth group '{options['auth_group']}'.")

        self.clear_invalid_devices_file()
        self.read_csv()

    def check_valid_auth_group(self, auth_group):
        exists = AuthorizationGroup.objects.filter(name=auth_group).exists()
        if not exists:
            logging.error(
                f"Authorization Group-Object: {auth_group} not in Database")
        return auth_group if exists else None

    def clear_invalid_devices_file(self):
        try:
            with open(SAVE_FILE, "w"):
                logging.info(f"Removing all entries in {SAVE_FILE}")
        except Exception as e:
            logging.error(
                f"Removing all entries in {SAVE_FILE} FAILED -> {e}"
            )

    def read_csv(self):
        try:
            with open(self.source_file, "r", newline="") as csvfile:
                logging.info(f"Reading {self.source_file}")
                reader = DictReader(csvfile, delimiter=";")
                for row in reader:
                    self.handle_deviceObject(row)
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
            logging.error(f"Error: Handling device Object failed -> {e}")

    def check_device(self, deviceObject):
        logging.info(f"Checking validity of device "
                     f"{deviceObject.get('appl-NAC-Hostname')}")
        try:
            if deviceObject.get('objectClass') != 'appl-NAC-Device':
                raise ValidationError(
                    f"Invalid Object-type! EXPECTED: appl-NAC-Device <->"
                    f" ACTUAL: {deviceObject.get('objectClass')}")
            with transaction.atomic():
                auth_group = AuthorizationGroup.objects.get(
                    name=self.auth_group
                )
                try:
                    deviceRoleProd = DeviceRoleProd.objects.get(
                        name=deviceObject.get("appl-NAC-DeviceRoleProd"))
                except ObjectDoesNotExist:
                    raise ValidationError(
                        f"DeviceRoleProd: "
                        f"{deviceObject.get('appl-NAC-DeviceRoleProd')} "
                        f"not in Database")
                try:
                    deviceRoleInst = DeviceRoleInst.objects.get(
                        name=deviceObject.get("appl-NAC-DeviceRoleInst"))
                except ObjectDoesNotExist:
                    raise ValidationError(
                        f"DeviceRoleInst: "
                        f"{deviceObject.get('appl-NAC-DeviceRoleInst')} "
                        f"not in Database")
                if deviceRoleProd not in auth_group.DeviceRoleProd.all():
                    raise ValidationError(
                        f"DeviceRoleProd: {deviceRoleProd} "
                        f"not in authorization group: {auth_group}")
                elif deviceRoleInst not in auth_group.DeviceRoleInst.all():
                    raise ValidationError(
                        f"DeviceRoleInst: {deviceRoleInst} "
                        f"not in authorization group: {auth_group}")

                device_data = {
                    "name": deviceObject.get("appl-NAC-Hostname"),
                    "authorization_group": auth_group,
                    "appl_NAC_DeviceRoleProd": deviceRoleProd,
                    "appl_NAC_DeviceRoleInst": deviceRoleInst,
                    "appl_NAC_FQDN": deviceObject.get("appl-NAC-FQDN"),
                    "appl_NAC_Hostname": deviceObject.get("appl-NAC-Hostname"),
                    "appl_NAC_Active": self.str_to_bool(
                        deviceObject.get("appl-NAC-Active")
                    ),
                    "appl_NAC_ForceDot1X": self.str_to_bool(
                        deviceObject.get("appl-NAC-ForceDot1X")
                    ),
                    "appl_NAC_Install": self.str_to_bool(
                        deviceObject.get("appl-NAC-Install")
                    ),
                    "appl_NAC_AllowAccessCAB": self.str_to_bool(
                        deviceObject.get("appl-NAC-AllowAccessCAB")
                    ),
                    "appl_NAC_AllowAccessAIR": self.str_to_bool(
                        deviceObject.get("appl-NAC-AllowAccessAIR")
                    ),
                    "appl_NAC_AllowAccessVPN": self.str_to_bool(
                        deviceObject.get("appl-NAC-AllowAccessVPN")
                    ),
                    "appl_NAC_AllowAccessCEL": self.str_to_bool(
                        deviceObject.get("appl-NAC-AllowAccessCEL")
                    ),
                    "appl_NAC_macAddressAIR": deviceObject.get(
                        "appl-NAC-macAddressAIR"
                    ),
                    "appl_NAC_macAddressCAB": deviceObject.get(
                        "appl-NAC-macAddressCAB"
                    ),
                    "appl_NAC_Certificate": deviceObject.get(
                        "appl-NAC-Certificate"
                    ),
                    "synchronized": self.str_to_bool(
                        deviceObject.get("synchronized")
                    )
                }
                device_form = DeviceForm(device_data)
                if device_form.is_valid():
                    logging.debug(f"Device {device_data.get('name')} is valid")
                    if Device.objects.filter(appl_NAC_Hostname=deviceObject.get('appl-NAC-Hostname')).exists():
                        logging.debug(f"Device {deviceObject.get('appl-NAC-Hostname')} already exists")
                        if self.update:
                            logging.debug(f"Updating Device {deviceObject.get('appl-NAC-Hostname')}")
                            Device.objects.filter(appl_NAC_Hostname=deviceObject.get('appl-NAC-Hostname')).delete()
                        else:
                            raise ValidationError(f"Device {deviceObject.get('appl-NAC-Hostname')} exists and will not get updated")
                    return device_data
                else:
                    logging.error(
                        f"Device {device_data.get('name')} is not valid"
                    )
                    for field, errors in device_form.errors.items():
                        for reason in errors:
                            logging.error(f"Field: {field} - Error: {reason}")
                            print(f"Field: {field} - Error: {reason}")
                    raise ValidationError("Invalid Device")
        except ValidationError:
            raise
        except Exception as e:
            logging.error(
                f"Checking validity of device {deviceObject.get('name')}: "
                f"FAILED -> {e}"
            )
            raise

    def str_to_bool(self, input_value):
        return not (input_value in {False, 'False', 'false', 'FALSE'})

    def add_device_to_db(self, deviceObject_valid):
        logging.info(
            f"Import device {deviceObject_valid.get('name')} to database"
        )
        try:
            with transaction.atomic():
                Device.objects.create(**deviceObject_valid)
                logging.debug(
                    f"Import device {deviceObject_valid.get('name')} to "
                    f"database: SUCCESSFUL"
                )
                return True
        except Exception:
            logging.error(
                f"Import device {deviceObject_valid.get('name')} to database: "
                f"FAILED"
            )
            return False

    def save_invalid_devices(self, deviceObject_invalid):
        try:
            column_header = deviceObject_invalid.keys()
            with open(SAVE_FILE, 'a', newline="") as csvfile:
                logging.info(f"Writing invalid device to {SAVE_FILE}")
                writer = DictWriter(
                    csvfile, fieldnames=column_header, delimiter=";"
                )
                if stat(SAVE_FILE).st_size == 0:
                    writer.writeheader()
                writer.writerows([deviceObject_invalid])
                logging.debug(
                    f"Writing invalid device to {SAVE_FILE}: "
                    f"SUCCESSFUL"
                )
        except Exception as e:
            logging.error(
                f"Writing invalid device to "
                f"{SAVE_FILE}: FAILED -> {e}"
            )
