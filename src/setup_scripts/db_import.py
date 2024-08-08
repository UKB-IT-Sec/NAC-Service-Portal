import logging
from os import environ, path as ospath, stat
from sys import path as syspath
from django import setup
from csv import DictReader, DictWriter
from django.db import transaction
from argparse import ArgumentParser

parent_dir = ospath.abspath(ospath.join(ospath.dirname(__file__), '..'))
syspath.insert(0, parent_dir)
environ.setdefault("DJANGO_SETTINGS_MODULE", "NAC_Service_Portal.settings")
setup()

from nac.models import Device, Area, SecurityGroup  # noqa: E402
from nac.forms import DeviceForm  # noqa: E402

CSV_SAVE_FILE = "ldap_objects.csv"
CSV_INVALID_DEVICES_FILE = "ldap_invalid_devices.csv"


def save_invalid_devices(deviceObjectDict):
    try:
        column_header = deviceObjectDict.keys()
        with open(CSV_INVALID_DEVICES_FILE, 'a', newline="") as csvfile:
            logging.info(f"Writing invalid device to {CSV_INVALID_DEVICES_FILE}")
            writer = DictWriter(
                csvfile, fieldnames=column_header, delimiter=";"
            )
            if stat(CSV_INVALID_DEVICES_FILE).st_size == 0:
                writer.writeheader()
            writer.writerows([deviceObjectDict])
            logging.debug(f"Writing invalid device to {CSV_INVALID_DEVICES_FILE}: SUCCESSFUL")
    except Exception as e:
        logging.error(f"Writing invalid device to {CSV_INVALID_DEVICES_FILE}: FAILED -> {e}")


def read_csv():
    try:
        with open(CSV_SAVE_FILE, "r", newline="") as csvfile:
            logging.info(f"Reading {CSV_SAVE_FILE}")
            reader = DictReader(csvfile, delimiter=";")
            for row in reader:
                if add_device_to_db(row):
                    pass
                else:
                    save_invalid_devices(row)
            logging.debug(f"Reading {CSV_SAVE_FILE}: SUCCESSFUL")
    except Exception as e:
        logging.error(f"Reading {CSV_SAVE_FILE}: FAILED -> {e}")


def str_to_bool(string):
    return string != 'False'


def add_device_to_db(deviceObject):
    logging.info(f"Import device {deviceObject.get('name')} to database")
    try:
        with transaction.atomic():
            if SecurityGroup.objects.filter(
                name=deviceObject.get("security_group")
            ).exists():
                security_group = SecurityGroup.objects.get(
                    name=deviceObject.get("security_group")
                )
            else:
                security_group = SecurityGroup.objects.create(
                    name=deviceObject.get("security_group")
                )
                logging.debug(f"Security Group {security_group} created successfully")
            if Area.objects.filter(name=deviceObject.get("area")).exists():
                area = Area.objects.get(name=deviceObject.get("area"))
            else:
                area = Area.objects.create(name=deviceObject.get("area"))
                area.security_group.set([SecurityGroup.objects.get(
                    name=deviceObject.get("security_group")
                )])
                logging.debug(f"Area {area} created successfully")
            device_data = {
                "name": deviceObject.get("name"),
                "area": area,
                "security_group": security_group,
                "appl_NAC_FQDN": deviceObject.get("appl_NAC_FQDN"),
                "appl_NAC_Hostname": deviceObject.get("appl_NAC_Hostname"),
                "appl_NAC_Active":
                    str_to_bool(deviceObject.get("appl_NAC_Active")),
                "appl_NAC_ForceDot1X":
                    str_to_bool(deviceObject.get("appl_NAC_ForceDot1x")),
                "appl_NAC_Install":
                    str_to_bool(deviceObject.get("appl_NAC_Install")),
                "appl_NAC_AllowAccessCAB":
                    str_to_bool(deviceObject.get("appl_NAC_AllowAccessCAB")),
                "appl_NAC_AllowAccessAIR":
                    str_to_bool(deviceObject.get("appl_NAC_AllowAccessAIR")),
                "appl_NAC_AllowAccessVPN":
                    str_to_bool(deviceObject.get("appl_NAC_AllowAccessVPN")),
                "appl_NAC_AllowAccessCEL":
                    str_to_bool(deviceObject.get("appl_NAC_AllowAccessCEL")),
                "appl_NAC_DeviceRoleProd":
                    deviceObject.get("appl_NAC_DeviceRoleProd"),
                "appl_NAC_DeviceRoleInst":
                    deviceObject.get("appl_NAC_DeviceRoleInst"),
                "appl_NAC_macAddressAIR":
                    deviceObject.get("appl_NAC_macAddressAIR"),
                "appl_NAC_macAddressCAB":
                    deviceObject.get("appl_NAC_macAddressCAB"),
                "appl_NAC_Certificate":
                    deviceObject.get("appl_NAC_Certificate"),
                "synchronized": str_to_bool(deviceObject.get("synchronized"))
            }
            logging.debug("Test device validity and create database entry")
            device_form = DeviceForm(device_data)
            if device_form.is_valid():
                Device.objects.create(**device_data)
                logging.debug(f"Device {device_data.get('name')} is valid")
                logging.info(f"Import device {deviceObject.get('name')} to database: SUCCESSFUL")
                return True
            else:
                logging.error(f"Device {device_data.get('name')} is not valid")
                for field, errors in device_form.errors.items():
                    for reason in errors:
                        logging.error(f"Field: {field} - Error: {reason}")
    except Exception:
        logging.error(f"Import device {deviceObject.get('name')} to database: FAILED")
        return False


def setup_logging():
    parser = ArgumentParser(description='Set the logging level')
    parser.add_argument(
        '--loglevel', default='ERROR',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        type=str.upper, help='Sets the logging level'
    )
    args = parser.parse_args()
    logging_level = getattr(logging, args.loglevel, None)
    logging.basicConfig(
        level=logging_level,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filename="db_import.log",
        filemode="w"
    )
    logging.info("Logger initialized")


if __name__ == "__main__":
    setup_logging()
    with open(CSV_INVALID_DEVICES_FILE, "w"):
        logging.info(f"Removed all entries in {CSV_INVALID_DEVICES_FILE}")
    read_csv()
