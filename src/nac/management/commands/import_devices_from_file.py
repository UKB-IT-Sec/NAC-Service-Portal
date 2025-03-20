import logging
from os.path import exists, getsize
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from nac.models import Device, AuthorizationGroup, DeviceRoleProd, DeviceRoleInst, DNSDomain
from nac.forms import DeviceForm
from helper.logging import setup_console_logger
from helper.filesystem import get_resources_directory, get_existing_path, get_config_directory
from helper.config import get_config_from_json
from helper.database import MacList
from nac.validation import normalize_mac
import traceback


DEFAULT_SOURCE_FILE = get_resources_directory() / 'deviceMatrix.xlsx'
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
            default='AuthGroupDefault',
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

    def get_set_or_default(self, json_config_key, deviceObject):
        if json_config_key['VALUE'] is not None:
            return json_config_key['VALUE']
        else:
            if json_config_key['SET'] is not None:
                return deviceObject.get(json_config_key['SET'])
            else:
                return deviceObject.get(json_config_key['DEFAULT'])

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
            logging.info(f"Reading {self.source_file}")
            data = pd.read_excel(self.source_file)

            for _, row in data.iterrows():
                self.handle_deviceObject(row.to_dict())

            logging.debug(f"Reading {self.source_file}: SUCCESSFUL")
        except Exception as e:
            logging.error(f"Reading {self.source_file}: FAILED -> {e}")

    def handle_deviceObject(self, deviceObject):
        try:
            device = self.check_device(deviceObject)
            if device:
                self.add_device_to_db(device)
        except ValidationError as e:
            self.save_invalid_devices(deviceObject, e)
        except Exception as e:
            logging.error(f"Error: Handling device Object failed -> {e}")
            traceback.print_exc()

    def get_DNS_domain(self, deviceObject):
        dnsdomain = self.get_set_or_default(self.csv_mapping['dns_domain'], deviceObject)
        try:
            Domain = DNSDomain.objects.get(name=dnsdomain)
        except ObjectDoesNotExist:
            raise ValidationError(f"DNS-Domain: {dnsdomain} not in Database")
        return Domain

    def get_deviceRole(self, deviceObject):
        DeviceRoleCriteria = self.csv_mapping['DeviceRoleCriteria']
        if DeviceRoleCriteria['MAPPING']:
            return self.get_deviceRole_from_ou_mapping(deviceObject)
        else:
            return self.get_deviceRole_from_csv_mapping(deviceObject)

    def int_conversion(self, value):
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def get_deviceRole_from_ou_mapping(self, deviceObject):
        DeviceRoleCriteria = self.csv_mapping['DeviceRoleCriteria']
        ou = self.get_set_or_default(DeviceRoleCriteria, deviceObject)

        if ou not in self.ou_mapping.keys():
            ou = self.ou_mapping["DEFAULT"]
        else:
            ou = self.ou_mapping[ou]

        try:
            deviceRoleProd = DeviceRoleProd.objects.get(name=ou['DeviceRoleProd'])
        except ObjectDoesNotExist:
            raise ValidationError(f"DeviceRoleProd: {ou['DeviceRoleProd']} not in Database")

        try:
            deviceRoleInst = DeviceRoleInst.objects.get(name=ou['DeviceRoleInst'])
        except ObjectDoesNotExist:
            raise ValidationError(f"DeviceRoleInst: {ou['DeviceRoleInst']} not in Database")

        return deviceRoleProd, deviceRoleInst

    def get_additional_info(self, json_config_key, deviceObject):
        if json_config_key['VALUE'] is not None:
            return json_config_key['VALUE']
        else:
            if json_config_key['SET'] is not None:
                add_info = {}
                for attribute in json_config_key['SET']:
                    add_info[attribute] = deviceObject.get(attribute)
                return add_info
            else:
                return deviceObject.get(json_config_key['DEFAULT'])

    def get_deviceRole_from_csv_mapping(self, deviceObject):
        deviceRoleProd = self.get_set_or_default(self.csv_mapping['appl-NAC-DeviceRoleProd'], deviceObject)
        deviceRoleInst = self.get_set_or_default(self.csv_mapping['appl-NAC-DeviceRoleInst'], deviceObject)

        try:
            deviceRoleProd = DeviceRoleProd.objects.get(name=deviceRoleProd)
        except ObjectDoesNotExist:
            raise ValidationError(f"DNS-Domain: {deviceRoleProd} not in Database")
        try:
            deviceRoleInst = DeviceRoleInst.objects.get(name=deviceRoleInst)
        except ObjectDoesNotExist:
            raise ValidationError(f"DNS-Domain: {deviceRoleInst} not in Database")
        return deviceRoleProd, deviceRoleInst

    def check_device(self, deviceObject):
        logging.info(f"Checking validity of device "
                     f"{self.get_set_or_default(self.csv_mapping['appl-NAC-Hostname'], deviceObject)}")
        try:
            """if self.get_set_or_default(self.csv_mapping['objectClass'], deviceObject) != 'appl-NAC-Device':
                raise ValidationError(
                    f"Invalid Object-type! EXPECTED: appl-NAC-Device <->"
                    f" ACTUAL: {self.get_set_or_default(self.csv_mapping['objectClass'], deviceObject)}")"""
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
                    "asset_id": "Test" + str(self.get_set_or_default(self.csv_mapping['asset_id'], deviceObject)),
                    "appl_NAC_Hostname": self.get_set_or_default(self.csv_mapping['appl-NAC-Hostname'], deviceObject) + normalize_mac(str(self.get_set_or_default(self.csv_mapping['appl-NAC-macAddressCAB'], deviceObject))),
                    "dns_domain": self.get_DNS_domain(deviceObject),
                    "authorization_group": auth_group,
                    "appl_NAC_DeviceRoleProd": deviceRoleProd,
                    "appl_NAC_DeviceRoleInst": deviceRoleInst,
                    "vlan": self.int_conversion(self.get_set_or_default(self.csv_mapping['vlan'], deviceObject)),
                    "appl_NAC_Active": self.str_to_bool(
                        self.get_set_or_default(self.csv_mapping['appl-NAC-Active'], deviceObject)
                    ),
                    "appl_NAC_ForceDot1X": self.str_to_bool(
                        self.get_set_or_default(self.csv_mapping['appl-NAC-ForceDot1X'], deviceObject)
                    ),
                    "appl_NAC_Install": self.str_to_bool(
                        self.get_set_or_default(self.csv_mapping['appl-NAC-Install'], deviceObject)
                    ),
                    "appl_NAC_AllowAccessCAB": self.str_to_bool(
                        self.get_set_or_default(self.csv_mapping['appl-NAC-AllowAccessCAB'], deviceObject)
                    ),
                    "appl_NAC_AllowAccessAIR": self.str_to_bool(
                        self.get_set_or_default(self.csv_mapping['appl-NAC-AllowAccessAIR'], deviceObject)
                    ),
                    "appl_NAC_AllowAccessVPN": self.str_to_bool(
                        self.get_set_or_default(self.csv_mapping['appl-NAC-AllowAccessVPN'], deviceObject)
                    ),
                    "appl_NAC_AllowAccessCEL": self.str_to_bool(
                        self.get_set_or_default(self.csv_mapping['appl-NAC-AllowAccessCEL'], deviceObject)
                    ),
                    "appl_NAC_macAddressAIR": (normalize_mac(str(value) if (value := self.get_set_or_default(self.csv_mapping['appl-NAC-macAddressAIR'], deviceObject)) is not None else None)),
                    "appl_NAC_macAddressCAB": (normalize_mac(str(value) if (value := self.get_set_or_default(self.csv_mapping['appl-NAC-macAddressCAB'], deviceObject)) is not None else None)),
                    "additional_info": self.get_additional_info(self.csv_mapping['additional_info'], deviceObject),
                }
                exists, device_id = self.mac_list.check_existing_mac(device_data)
                if exists:
                    logging.debug(f"Device {device_data.get('appl_NAC_Hostname')} already exists")
                    device_form = DeviceForm(device_data, instance=Device.objects.get(id=device_id))
                else:
                    device_form = DeviceForm(device_data)
                if device_form.is_valid():
                    """logging.debug(f"Device {device_data.get('appl_NAC_Hostname')} is valid")   
                    if exists:
                        if self.update:
                            logging.debug(f"Updating Device {device_data.get('appl_NAC_Hostname')}")
                            device_form.save()
                            return None
                        else:
                            raise ValidationError(f"Device {device_data.get('appl_NAC_Hostname')} exists and will not get updated")
                    else:
                        return device_form.cleaned_data"""
                else:
                    logging.error(
                        f"Device {device_data.get('appl_NAC_Hostname')} is not valid"
                    )
                    form_errors = {}
                    for field, errors in device_form.errors.items():
                        form_errors[field] = []
                        for reason in errors:
                            logging.error(f"Field: {field} - Error: {reason}")
                            form_errors[field].append(reason)
                    raise ValidationError(form_errors)
        except ValidationError:
            raise
        except Exception as e:
            logging.error(
                f"Checking validity of device {self.get_set_or_default(self.csv_mapping['appl-NAC-Hostname'], deviceObject)}: "
                f"FAILED -> {e}"
            )
            raise

    def str_to_bool(self, input_value):
        return not (input_value in {False, 'False', 'false', 'FALSE', 'EFRE INAK'})

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

    def save_invalid_devices(self, deviceObject_invalid, error_message):
        try:
            logging.info(f"Writing invalid device to {DEFAULT_SAVE_FILE}")
            deviceObject_invalid['error_message'] = error_message
            data = pd.DataFrame([deviceObject_invalid])
            file_is_empty = exists(DEFAULT_SAVE_FILE) and getsize(DEFAULT_SAVE_FILE) == 0
            if exists(DEFAULT_SAVE_FILE) and not file_is_empty:
                data.to_csv(DEFAULT_SAVE_FILE, mode='a', header=False, index=False, sep=';')
            else:
                data.to_csv(DEFAULT_SAVE_FILE, mode='w', header=True, index=False, sep=';')

            logging.debug(f"Writing invalid device to {DEFAULT_SAVE_FILE}: SUCCESSFUL")
        except Exception as e:
            logging.error(f"Writing invalid device to {DEFAULT_SAVE_FILE}: FAILED -> {e}")
