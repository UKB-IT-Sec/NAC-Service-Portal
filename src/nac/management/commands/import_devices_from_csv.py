import logging
from os import stat
from csv import DictReader, DictWriter
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from nac.models import Device, AuthorizationGroup, DeviceRoleProd, DeviceRoleInst
from nac.forms import DeviceForm
from helper.logging import setup_console_logger
from helper.filesystem import get_resources_directory, get_existing_path, get_config_directory
from helper.config import get_config_from_json
from helper.database import MacList
import traceback


DEFAULT_SOURCE_FILE = get_resources_directory() / 'ldapObjects.csv'
DEFAULT_SAVE_FILE = get_resources_directory() / "invalid_devices.csv"
DEFAULT_CSV_MAPPING = get_config_directory() / 'csv_mapping.json'
DEFAULT_OU_MAPPING = get_config_directory() / 'ou_mapping.json'


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
        parser.add_argument(
            '-c', '--csv_config',
            default=DEFAULT_CSV_MAPPING,
            help='use a specific config file [src/csv_mapping.cfg]')
        parser.add_argument(
            '-o', '--ou_config',
            default=DEFAULT_OU_MAPPING,
            help='use a specific config file [src/ou_mapping.cfg]')

    def handle(self, *args, **options):
        setup_console_logger(options['verbosity'])
        self.source_file = get_existing_path(options['csv_file'])
        self.update = options['update']
        self.csv_mapping = get_config_from_json(options['csv_config'])
        self.ou_mapping = get_config_from_json(options['ou_config'])
        self.mac_list = MacList()
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

    def get_set_or_default(self, json_config_key):
        if json_config_key['SET'] is not None:
            return json_config_key['SET']
        else:
            return json_config_key['DEFAULT']

    def check_valid_auth_group(self, auth_group):
        exists = AuthorizationGroup.objects.filter(name=auth_group).exists()
        if not exists:
            logging.error(
                f"Authorization Group-Object: {auth_group} not in Database")
        return auth_group if exists else None

    def clear_invalid_devices_file(self):
        try:
            with open(DEFAULT_SAVE_FILE, "w"):
                logging.info(f"Removing all entries in {DEFAULT_SAVE_FILE}")
        except Exception as e:
            logging.error(
                f"Removing all entries in {DEFAULT_SAVE_FILE} FAILED -> {e}"
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
            if device:
                self.add_device_to_db(device)
        except ValidationError as e:
            logging.error(f"Invalid Device -> {e}")
            self.save_invalid_devices(deviceObject)
        except Exception as e:
            logging.error(f"Error: Handling device Object failed -> {e}")
            traceback.print_exc()

    def get_deviceRole(self, deviceObject):
        DeviceRoleCriteria = self.csv_mapping['DeviceRoleCriteria']
        if DeviceRoleCriteria['MAPPING']:  # True -> DeviceRoles based on OU-Mapping, False -> DeviceRoles based on CSV-Mapping
            ou = deviceObject.get(self.get_set_or_default(DeviceRoleCriteria))
            if ou not in self.ou_mapping.keys():
                ou = self.ou_mapping["DEFAULT"]
            else:
                ou = self.ou_mapping[ou]
            try:
                deviceRoleProd = DeviceRoleProd.objects.get(
                    name=ou['DeviceRoleProd'])
            except ObjectDoesNotExist:
                raise ValidationError(
                    f"DeviceRoleProd: "
                    f"{ou['DeviceRoleProd']} "
                    f"not in Database")
            try:
                deviceRoleInst = DeviceRoleInst.objects.get(
                    name=ou['DeviceRoleInst'])
            except ObjectDoesNotExist:
                raise ValidationError(
                    f"DeviceRoleInst: "
                    f"{ou['DeviceRoleInst']} "
                    f"not in Database")
        else:
            deviceRoleProd = self.get_set_or_default(self.csv_mapping['appl-NAC-DeviceRoleProd'])
            deviceRoleInst = self.get_set_or_default(self.csv_mapping['appl-NAC-DeviceRoleInst'])
            try:
                deviceRoleProd = DeviceRoleProd.objects.get(
                    name=deviceObject.get(deviceRoleProd))
            except ObjectDoesNotExist:
                raise ValidationError(
                    f"DeviceRoleProd: "
                    f"{deviceObject.get(deviceRoleProd)} "
                    f"not in Database")
            try:
                deviceRoleInst = DeviceRoleInst.objects.get(
                    name=deviceObject.get(deviceRoleInst))
            except ObjectDoesNotExist:
                raise ValidationError(
                    f"DeviceRoleInst: "
                    f"{deviceObject.get(deviceRoleInst)} "
                    f"not in Database")
        return deviceRoleProd, deviceRoleInst

    def check_device(self, deviceObject):
        logging.info(f"Checking validity of device "
                     f"{deviceObject.get(self.get_set_or_default(self.csv_mapping['appl-NAC-Hostname']))}")
        try:
            if deviceObject.get(self.get_set_or_default(self.csv_mapping['objectClass'])) != 'appl-NAC-Device':
                raise ValidationError(
                    f"Invalid Object-type! EXPECTED: appl-NAC-Device <->"
                    f" ACTUAL: {deviceObject.get(self.get_set_or_default(self.csv_mapping['objectClass']))}")
            with transaction.atomic():
                auth_group = AuthorizationGroup.objects.get(
                    name=self.auth_group
                )
                deviceRoleProd, deviceRoleInst = self.get_deviceRole(deviceObject)
                if deviceRoleProd not in auth_group.DeviceRoleProd.all():
                    raise ValidationError(
                        f"DeviceRoleProd: {deviceRoleProd} "
                        f"not in authorization group: {auth_group}")
                elif deviceRoleInst not in auth_group.DeviceRoleInst.all():
                    raise ValidationError(
                        f"DeviceRoleInst: {deviceRoleInst} "
                        f"not in authorization group: {auth_group}")

                device_data = {
                    "name": deviceObject.get(self.get_set_or_default(self.csv_mapping['appl-NAC-Hostname'])),
                    "authorization_group": auth_group,
                    "appl_NAC_DeviceRoleProd": deviceRoleProd,
                    "appl_NAC_DeviceRoleInst": deviceRoleInst,
                    "appl_NAC_FQDN": deviceObject.get(self.get_set_or_default(self.csv_mapping['appl-NAC-FQDN'])),
                    "appl_NAC_Hostname": deviceObject.get(self.get_set_or_default(self.csv_mapping['appl-NAC-Hostname'])),
                    "appl_NAC_Active": self.str_to_bool(
                        deviceObject.get(self.get_set_or_default(self.csv_mapping['appl-NAC-Active']))
                    ),
                    "appl_NAC_ForceDot1X": self.str_to_bool(
                        deviceObject.get(self.get_set_or_default(self.csv_mapping['appl-NAC-ForceDot1X']))
                    ),
                    "appl_NAC_Install": self.str_to_bool(
                        deviceObject.get(self.get_set_or_default(self.csv_mapping['appl-NAC-Install']))
                    ),
                    "appl_NAC_AllowAccessCAB": self.str_to_bool(
                        deviceObject.get(self.get_set_or_default(self.csv_mapping['appl-NAC-AllowAccessCAB']))
                    ),
                    "appl_NAC_AllowAccessAIR": self.str_to_bool(
                        deviceObject.get(self.get_set_or_default(self.csv_mapping['appl-NAC-AllowAccessAIR']))
                    ),
                    "appl_NAC_AllowAccessVPN": self.str_to_bool(
                        deviceObject.get(self.get_set_or_default(self.csv_mapping['appl-NAC-AllowAccessVPN']))
                    ),
                    "appl_NAC_AllowAccessCEL": self.str_to_bool(
                        deviceObject.get(self.get_set_or_default(self.csv_mapping['appl-NAC-AllowAccessCEL']))
                    ),
                    "appl_NAC_macAddressAIR": deviceObject.get(
                        self.get_set_or_default(self.csv_mapping['appl-NAC-macAddressAIR'])
                    ),
                    "appl_NAC_macAddressCAB": deviceObject.get(
                        self.get_set_or_default(self.csv_mapping['appl-NAC-macAddressCAB'])
                    ),
                    "appl_NAC_Certificate": deviceObject.get(
                        self.get_set_or_default(self.csv_mapping['appl-NAC-Certificate'])
                    ),
                    "synchronized": self.str_to_bool(
                        deviceObject.get(self.get_set_or_default(self.csv_mapping['synchronized']))
                    )
                }
                device_form = DeviceForm(device_data)
                if device_form.is_valid():
                    logging.debug(f"Device {device_data.get('name')} is valid")
                    exists, device_id = self.mac_list.check_existing_mac(device_form.cleaned_data)
                    if exists:
                        logging.debug(f"Device {device_data.get('appl_NAC_Hostname')} already exists")
                        if self.update:
                            logging.debug(f"Updating Device {device_data.get('appl_NAC_Hostname')}")
                            Device.objects.filter(id=device_id).update(**device_form.cleaned_data)
                            return None
                        else:
                            raise ValidationError(f"Device {device_data.get('appl_NAC_Hostname')} exists and will not get updated")
                    return device_form.cleaned_data
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
                f"Checking validity of device {deviceObject.get(self.get_set_or_default(self.csv_mapping['appl-NAC-Hostname']))}: "
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
                new_device = Device.objects.create(**deviceObject_valid)
                self.mac_list.update_mac_list(new_device.__dict__)
                logging.debug(
                    f"Import device {deviceObject_valid.get('name')} to "
                    f"database: SUCCESSFUL"
                )
                return True
        except Exception as e:
            logging.error(
                f"Import device {deviceObject_valid.get('name')} to database: "
                f"FAILED -> {e}"
            )
            return False

    def save_invalid_devices(self, deviceObject_invalid):
        try:
            column_header = deviceObject_invalid.keys()
            with open(DEFAULT_SAVE_FILE, 'a', newline="") as csvfile:
                logging.info(f"Writing invalid device to {DEFAULT_SAVE_FILE}")
                writer = DictWriter(
                    csvfile, fieldnames=column_header, delimiter=";"
                )
                if stat(DEFAULT_SAVE_FILE).st_size == 0:
                    writer.writeheader()
                writer.writerows([deviceObject_invalid])
                logging.debug(
                    f"Writing invalid device to {DEFAULT_SAVE_FILE}: "
                    f"SUCCESSFUL"
                )
        except Exception as e:
            logging.error(
                f"Writing invalid device to "
                f"{DEFAULT_SAVE_FILE}: FAILED -> {e}"
            )
