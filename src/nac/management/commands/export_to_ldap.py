'''
    NSSP - Export to ldap server
    Copyright (C) 2024 Universitaetsklinikum Bonn AoeR

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
import logging
from django.core.management.base import BaseCommand

from helper.filesystem import get_config_directory
from nac.models import Device
from helper.config import get_config_from_file
from helper.logging import setup_console_logger
from helper.ldap import connect_to_ldap_server


DEFAULT_CONFIG = get_config_directory() / 'export.cnf'


class Command(BaseCommand):
    help = "Export Devices to LDAP server"

    def add_arguments(self, parser):
        parser.add_argument('-c', '--config_file', default=DEFAULT_CONFIG, help='use a specific config file [src/export.cnf]')

    def handle(self, *args, **options):
        setup_console_logger(options['verbosity'])
        self.config = get_config_from_file(options['config_file'])

        devices_to_sync = self._get_all_changed_devices()

        self.ldap_connection = connect_to_ldap_server(
            self.config['ldap-server']['address'],
            self.config['ldap-server']['user'],
            self.config['ldap-server']['password'],
            port=int(self.config['ldap-server']['port']),
            tls=self.config['ldap-server'].getboolean('tls')
            )

        for entry in devices_to_sync:
            self._add_or_update_device_in_ldap_database(entry)

        self.ldap_connection.unbind()

    def _get_all_changed_devices(self):
        return Device.objects.all().filter(synchronized=False)

    def _add_or_update_device_in_ldap_database(self, device):
        logging.debug('processing %s', device.name)
        if self._device_exists(device.name):
            self._delete_device(device)
        self._add_device(device)

    def _device_exists(self, devicename):
        return self.ldap_connection.search('appl-NAC-Hostname={},ou=Devices,dc=ukbonn,dc=de'.format(devicename), '(objectclass=appl-NAC-Device)')

    def _delete_device(self, device):
        if self.ldap_connection.delete('appl-NAC-Hostname={},ou=Devices,dc=ukbonn,dc=de'.format(device.name)):
            logging.info('%s deleted', device.name)
        else:
            logging.error('failed to delete %s', device.name)

    def _add_device(self, device):
        if self.ldap_connection.add('appl-NAC-Hostname={},ou=Devices,dc=ukbonn,dc=de'.format(device.name),
                                    'appl-NAC-Device',
                                    self._map_device_data(device)
                                    ):
            logging.info('%s added', device.name)
            device.synchronized = True
            device.save()
            return True
        else:
            logging.error('failed to add %s', device.name)
        return False

    def _map_device_data(self, device):
        device_data = {
            'appl-NAC-FQDN': device.appl_NAC_FQDN,
            'appl-NAC-Hostname': device.appl_NAC_Hostname,
            'appl-NAC-Active': device.appl_NAC_Active,
            'appl-NAC-ForceDot1X': device.appl_NAC_ForceDot1X,
            'appl-NAC-Install': device.appl_NAC_Install,
            'appl-NAC-AllowAccessCAB': device.appl_NAC_AllowAccessCAB,
            'appl-NAC-AllowAccessAIR': device.appl_NAC_AllowAccessAIR,
            'appl-NAC-AllowAccessVPN': device.appl_NAC_AllowAccessVPN,
            'appl-NAC-AllowAccessCEL': device.appl_NAC_AllowAccessCEL
            }
        if device.appl_NAC_DeviceRoleProd:
            device_data['appl-NAC-DeviceRoleProd'] = device.appl_NAC_DeviceRoleProd
        if device.appl_NAC_DeviceRoleInst:
            device_data['appl-NAC-DeviceRoleInst'] = device.appl_NAC_DeviceRoleInst
        if device.appl_NAC_macAddressCAB:
            device_data['appl-NAC-macAddressCAB'] = device.appl_NAC_macAddressCAB
        if device.appl_NAC_macAddressAIR:
            device_data['appl-NAC-macAddressAIR'] = device.appl_NAC_macAddressAIR
        if device.appl_NAC_Certificate:
            device_data['appl-NAC-Certificate'] = device.appl_NAC_Certificate
        return device_data
