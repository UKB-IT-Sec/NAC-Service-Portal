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
import argparse
import sys
import logging

from helper.filesystem import get_src_directory


PROGRAM_NAME = 'NSSP - Export to LDAP Server'
PROGRAM_DESCRIPTION = 'export all content to ldap server, that is marked as changed.'

DEFAULT_CONFIG = get_src_directory() / 'export.cnf'


def setup_argparser():
    parser = argparse.ArgumentParser(description='{} - {}'.format(PROGRAM_NAME, PROGRAM_DESCRIPTION))
    parser.add_argument('-c', '--config_file', default=DEFAULT_CONFIG, help='use a specific config file [src/export.cnf]')
    return parser.parse_args()


if __name__ == '__main__':

    args = setup_argparser()
    logging.debug('using conf file: {}'.format(args.config_file))

    sys.exit(0)
