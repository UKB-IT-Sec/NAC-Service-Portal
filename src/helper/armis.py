from helper.config import get_config_from_file
from helper.filesystem import get_config_directory
from armis import ArmisCloud
import re

global_acloud = None
armis_config = get_config_from_file(get_config_directory() / 'export.cnf')


def get_or_create_armis_cloud():
    global global_acloud
    if global_acloud is None:
        global_acloud = ArmisCloud(
            api_secret_key=armis_config['armis-server']['api_secret_key'],
            tenant_hostname=armis_config['armis-server']['tenant_hostname']
        )
    return global_acloud


def _filter_sort_sites(sites):
    pattern = rf'{armis_config['armis-server']['sites_pattern']}'
    filtered_sites = {key: value for key, value in sites.items() if re.match(pattern, value['name'])}
    return dict(sorted(filtered_sites.items(), key=lambda x: x[1]['name']))


def get_armis_sites():
    acloud = get_or_create_armis_cloud()
    return _filter_sort_sites(acloud.get_sites())


def get_devices(site):
    acloud = get_or_create_armis_cloud()
    vlan_bl = ""
    vlan_blacklist = armis_config['armis-server'].get('vlan_blacklist', '')
    vlan_bl = f"!networkInterface:(vlans:{vlan_blacklist})" if vlan_blacklist else ""
    return acloud.get_devices(
        asq=f'in:devices site:"{site.get('name')}" timeFrame:"7 Days" {vlan_bl}',
        fields=['id', 'ipAddress', 'name']
    )
