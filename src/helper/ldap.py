'''
    NSSP
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
from ldap3 import Server, Connection, ALL
from ldap3.utils.log import set_library_log_detail_level, EXTENDED
import logging


def connect_to_ldap_server(address, username, password, port=389, tls=False):
    set_library_log_detail_level(EXTENDED)
    logging.info('connecting to LDAP server: {}:{} user: {}'.format(address, port, username))
    ldap_server = Server(address, port=port, use_ssl=tls, get_info=ALL)
    ldap_connection = Connection(ldap_server, username, password)
    ldap_connection.bind()
    return ldap_connection