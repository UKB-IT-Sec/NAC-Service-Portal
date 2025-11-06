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


def connect_to_ldap_server(address, username, password, port=636, tls=False):
    set_library_log_detail_level(EXTENDED)
    logging.info('connecting to LDAP server: {}:{} user: {}'.format(address, port, username))
    ldap_server = Server(address, port=port, use_ssl=tls, get_info=ALL)
    ldap_connection = Connection(ldap_server, username, password)
    ldap_connection.bind()
    return ldap_connection


def device_exists(device_fqdn, ldap_connection, search_base):
    return ldap_connection.search('appl-NAC-AssetID={},{}'.format(device_fqdn, search_base), '(objectclass=appl-NAC-Device)')


def delete_device(device_fqdn, ldap_connection, search_base):
    if ldap_connection.delete('appl-NAC-AssetID={},{}'.format(device_fqdn, search_base)):
        logging.info('%s deleted', device_fqdn)
    else:
        logging.error('failed to delete %s', device_fqdn)


def map_device_data(device):

    device_data = {
        'appl-NAC-AssetID': device.asset_id,
        'appl-NAC-Hostname': device.appl_NAC_Hostname,
        'appl-NAC-FQDN': f'{device.appl_NAC_Hostname}.{device.dns_domain}',
        'appl-NAC-Deleted': device.deleted,
        'appl-NAC-Active': device.appl_NAC_Active,
        'appl-NAC-ForceDot1X': device.appl_NAC_ForceDot1X,
        'appl-NAC-Install': device.appl_NAC_Install,
        'appl-NAC-AllowAccessCAB': device.appl_NAC_AllowAccessCAB,
        'appl-NAC-AllowAccessAIR': device.appl_NAC_AllowAccessAIR,
        'appl-NAC-AllowAccessVPN': device.appl_NAC_AllowAccessVPN,
        'appl-NAC-AllowAccessCEL': device.appl_NAC_AllowAccessCEL,
        'appl-NAC-LastModified': device.last_modified,
        'appl-NAC-CreationDate': device.creationDate

        }
    if device.appl_NAC_DeviceRoleProd:
        device_data['appl-NAC-DeviceRoleProd'] = device.appl_NAC_DeviceRoleProd.__str__()
    if device.appl_NAC_macAddressAIR:
        device_data['appl-NAC-macAddressAIR'] = device.appl_NAC_macAddressAIR.split(',')
    if device.appl_NAC_macAddressCAB:
        device_data['appl-NAC-macAddressCAB'] = device.appl_NAC_macAddressCAB.split(',')

    return device_data
