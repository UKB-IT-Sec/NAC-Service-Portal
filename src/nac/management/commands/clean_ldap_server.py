'''
    NSSP - Clean ldap server
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
from django.core.exceptions import ObjectDoesNotExist
from ldap3 import SUBTREE

from helper.filesystem import get_config_directory
from nac.models import Device
from helper.config import get_config_from_file
from helper.logging import setup_console_logger
from helper.ldap import connect_to_ldap_server, delete_device


DEFAULT_CONFIG = get_config_directory() / 'ldap.cfg'


class Command(BaseCommand):
    help = "Remove devices on ldap not present in NSSP"

    def add_arguments(self, parser):
        parser.add_argument('-c', '--config_file', default=DEFAULT_CONFIG, help='use a specific config file [src/ldap.cfg]')
        parser.add_argument('-d', '--dry_run', action='store_true', help='do not delete devices on ldap')

    def handle(self, *args, **options):
        setup_console_logger(options['verbosity'])
        self.config = get_config_from_file(options['config_file'])

        self.ldap_connection = connect_to_ldap_server(
            self.config['ldap-server']['address'],
            self.config['ldap-server']['user'],
            self.config['ldap-server']['password'],
            port=int(self.config['ldap-server']['port']),
            tls=self.config['ldap-server'].getboolean('tls')
            )

        entry_generator = self.ldap_connection.extend.standard.paged_search(search_base=self.config['ldap-server']['search_base'],
                                                                            search_filter='(objectClass=appl-NAC-Device)',
                                                                            search_scope=SUBTREE,
                                                                            attributes=['appl-NAC-FQDN'],
                                                                            paged_size=5,
                                                                            generator=True)
        for entry in entry_generator:
            logging.debug('checking device %s', entry['attributes']['appl-NAC-FQDN'])
            try:
                Device.objects.get(appl_NAC_Hostname=entry['attributes']['appl-NAC-FQDN'])
            except ObjectDoesNotExist:
                if options['dry_run']:
                    logging.warning('%s would be deleted (DRY RUN)', entry['attributes']['appl-NAC-FQDN'])
                else:
                    delete_device(entry['attributes']['appl-NAC-FQDN'], self.ldap_connection, self.config['ldap-server']['search_base'])

        self.ldap_connection.unbind()
