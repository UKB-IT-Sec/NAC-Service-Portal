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
from django.core.management.base import BaseCommand

from helper.filesystem import get_config_directory
from nac.models import Device


DEFAULT_CONFIG = get_config_directory() / 'export.cnf'


class Command(BaseCommand):
    help = "Export Devices to LDAP server"

    def add_arguments(self, parser):
        parser.add_argument('-c', '--config_file', default=DEFAULT_CONFIG, help='use a specific config file [src/export.cnf]')

    def handle(self, *args, **options):
        self.stdout.write("conf file used:{}".format(options['config_file']))
        devices_to_sync = self._get_all_changed_devices()
        for entry in devices_to_sync:
            self._add_or_update_device_in_ldap_database(entry)

    def _get_all_changed_devices(self):
        return Device.objects.all().filter(synchronized=False)

    def _add_or_update_device_in_ldap_database(self, device):
        self.stdout.write('syncing device: {}'.format(device))
        pass
