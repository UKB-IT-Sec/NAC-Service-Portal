from helper.config import get_config_from_file
from helper.filesystem import get_config_directory
from armis import ArmisCloud
from .database import MacList
import re
from functools import wraps

armis_config = get_config_from_file(get_config_directory() / 'armis.cfg')


def armiscloud(func):
    global global_acloud
    global_acloud = None

    @wraps(func)
    def get_or_create_armis_cloud(*args, **kwargs):
        global global_acloud
        if global_acloud is None:
            global_acloud = ArmisCloud(
                api_secret_key=armis_config['armis-server']['api_secret_key'],
                tenant_hostname=armis_config['armis-server']['tenant_hostname']
            )
        return func(global_acloud, *args, **kwargs)
    return get_or_create_armis_cloud


def _filter_sort_sites(sites):
    pattern = rf"{armis_config['armis-server']['sites_pattern']}"
    filtered_sites = {key: value for key, value in sites.items() if re.match(pattern, value['name'])}
    return dict(sorted(filtered_sites.items(), key=lambda x: x[1]['name']))


@armiscloud
def get_armis_sites(acloud):
    return _filter_sort_sites(acloud.get_sites())


def _remove_existing_devices(deviceList):
    _mac_list = MacList()
    return [device for device in deviceList if not _mac_list.check_existing_mac(device)[0]]

# flake8: noqa: E231
@armiscloud
def get_devices(acloud, sites):
    vlan_bl = ""
    vlan_blacklist = armis_config['armis-server'].get('vlan_blacklist', '')
    vlan_bl = f"!networkInterface:(vlans:{vlan_blacklist})" if vlan_blacklist else ""
    sites = ','.join(f'"{site}"' for site in sites)
    deviceList = acloud.get_devices(
        asq=f'in:devices site:{sites} timeFrame:"7 Days" {vlan_bl}',
        fields_wanted=['id', 'ipAddress', 'macAddress', 'name', 'boundaries']
    )
    return _remove_existing_devices(deviceList)
# flake8: qa


def get_boundaries(deviceList):
    unique_boundaries = set()
    for device in deviceList:
        boundaries = [b.strip() for b in device['boundaries'].split(',')]
        unique_boundaries.update(boundaries)
        
    return sorted(list(unique_boundaries))

def get_tenant_url():
    return 'https://{}'.format(armis_config['armis-server']['tenant_hostname'])

def map_ids_to_names(selectedSiteIds, armisServerSites):
    return [armisServerSites[id]['name'] for id in selectedSiteIds if id in armisServerSites]
