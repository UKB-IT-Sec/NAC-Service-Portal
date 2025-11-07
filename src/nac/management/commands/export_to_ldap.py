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
from helper.ldap import connect_to_ldap_server, delete_device, device_exists, map_device_data


DEFAULT_CONFIG = get_config_directory() / 'ldap.cfg'


class Command(BaseCommand):
    help = "Export Devices to LDAP server"

    def add_arguments(self, parser):
        parser.add_argument('-c', '--config_file', default=DEFAULT_CONFIG, help='use a specific config file [src/ldap.cfg]')
        parser.add_argument('-a', '--all', action='store_true', help='sync all devices')
        parser.add_argument('-d', '--dry-run', action='store_true', help='see all affected device')

    def handle(self, *args, **options):
        setup_console_logger(options['verbosity'])
        self.config = get_config_from_file(options['config_file'])

        if options['all']:
            devices_to_sync = Device.objects.all()
        else:
            devices_to_sync = self._get_all_changed_devices()

        self.ldap_connection = connect_to_ldap_server(
            self.config['ldap-server']['address'],
            self.config['ldap-server']['user'],
            self.config['ldap-server']['password'],
            port=int(self.config['ldap-server']['port']),
            tls=self.config['ldap-server'].getboolean('tls')
            )

        for entry in devices_to_sync:
            self._add_or_update_device_in_ldap_database(entry, dry_run=options['dry_run'])

        self.ldap_connection.unbind()

    def _get_all_changed_devices(self):
        return Device.objects.all().filter(synchronized=False)

    def _add_device(self, device):
        if device.allowLdapSync:
            add_dn = 'appl-NAC-AssetID={},{}'.format(f'{device.asset_id}', self.config['ldap-server']['search_base'])
            logging.debug('LDAP DN for new Device: %s', add_dn)
            if self.ldap_connection.add(add_dn,
                                        'appl-NAC-Device',
                                        map_device_data(device)):
                logging.info('Device %s added with ID %s ', device.appl_NAC_Hostname, device.asset_id)
                device.synchronized = True
                device.save()
                return True
            else:
                logging.error('failed to add Device %s with ID %s ', device.appl_NAC_Hostname, device.asset_id)
            return False
        else:
            logging.error('Device %s with ID %s not allowed to Sync', device.appl_NAC_Hostname, device.asset_id)

    def _add_or_update_device_in_ldap_database(self, device, dry_run=False):
        logging.debug('processing %s', device.asset_id)
        if dry_run:
            logging.info('Dry-run: would add/update device %s', device.asset_id)
            return True
        else:
            if device_exists(f'{device.asset_id}', self.ldap_connection, self.config['ldap-server']['search_base']):
                delete_device(f'{device.asset_id}', self.ldap_connection, self.config['ldap-server']['search_base'])
            return self._add_device(device)
