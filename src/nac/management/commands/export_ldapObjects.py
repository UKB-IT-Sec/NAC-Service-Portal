from django.core.management.base import BaseCommand
import logging
from helper.filesystem import get_config_directory
from helper.config import get_config_from_file
from helper.logging import setup_console_logger
from helper.ldap import connect_to_ldap_server
from ldap3 import SUBTREE
from csv import DictWriter
from os import stat

DEFAULT_CONFIG = get_config_directory() / 'export.cnf'
DEFAULT_OBJECT = 'inetOrgPerson'
CSV_SAVE_FILE = 'ldapObjects.csv'


class Command(BaseCommand):
    help = "Export objects from LDAP server"

    def add_arguments(self, parser):
        parser.add_argument('-c', '--config_file',
                            default=DEFAULT_CONFIG,
                            help='use a specific config file [src/export.cnf]')
        parser.add_argument('-o', '--objectclass',
                            default=DEFAULT_OBJECT,
                            help='specify which object to export')

    def handle(self, *args, **options):
        setup_console_logger(options['verbosity'])
        self.config = get_config_from_file(options['config_file'])
        self.objectClass = options['objectclass']
        self._clear_file()

        self.ldap_connection = connect_to_ldap_server(
            self.config['ldap-server']['address'],
            self.config['ldap-server']['user'],
            self.config['ldap-server']['password'],
            port=int(self.config['ldap-server']['port']),
            tls=self.config['ldap-server'].getboolean('tls')
            )
        self._get_objects()
        self._handle_objects()

        self.ldap_connection.unbind()

    def _handle_objects(self):
        logging.info('Initiating CSV export to file: %s', CSV_SAVE_FILE)
        for progress_counter, entry in enumerate(self.ldap_connection.entries):
            self.write_object(
                entry.entry_attributes_as_dict, progress_counter+1)

    def _get_objects(self):
        logging.debug('Searching for %s-objects', self.objectClass)
        search_result = self.ldap_connection.search(
            'dc=ukbonn,dc=de', '(objectclass={})'.format(self.objectClass),
            SUBTREE, attributes=['*'])
        self.entry_count = len(self.ldap_connection.response)
        if search_result:
            logging.info('Found: %s-objects - Count: %i',
                         self.objectClass, self.entry_count)
        else:
            logging.error("Not Found: %s-objects",
                          self.objectClass)

    def _convert_dictlists_to_str(self, dict):
        return {key: ','.join(value) if isinstance(value, list)
                else str(value) for key, value in dict.items()}

    def _clear_file(self):
        try:
            logging.info('Truncating %s', CSV_SAVE_FILE)
            with open(CSV_SAVE_FILE, 'w'):
                pass
        except Exception as e:
            logging.error('Failed to truncate %s -> %s', CSV_SAVE_FILE, str(e))

    def write_object(self, object_as_dict, progress_counter):
        try:
            column_header = object_as_dict.keys()
            with open(CSV_SAVE_FILE, 'a', newline="") as csvfile:
                writer = DictWriter(
                    csvfile, fieldnames=column_header, delimiter=';')
                if stat(CSV_SAVE_FILE).st_size == 0:
                    writer.writeheader()
                writer.writerows(
                    [self._convert_dictlists_to_str(object_as_dict)])
                logging.debug(
                    'Successfully exported object %i/%i to file: %s ',
                    progress_counter, self.entry_count, CSV_SAVE_FILE,)
        except Exception as e:
            logging.error(
                'Failed to export object to file: %s -> %s',
                CSV_SAVE_FILE, str(e))
