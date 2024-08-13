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
            port = int(self.config['ldap-server']['port']),
            tls= self.config['ldap-server'].getboolean('tls')
            )
        for entry in devices_to_sync:
            self._add_or_update_device_in_ldap_database(entry)

    def _get_all_changed_devices(self):
        return Device.objects.all().filter(synchronized=False)

    def _add_or_update_device_in_ldap_database(self, device):
        logging.info('syncing device: {}'.format(device))     
