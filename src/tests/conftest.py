import pytest

from nac.models import AdministrationGroup, DeviceRoleProd, DNSDomain, Device

from django.core.management import call_command


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command('loaddata', 'devices_test_data.json')


@pytest.mark.django_db
@pytest.fixture(scope="function")
def sample_device_role_prod():
    """
    Creates a DeviceRoleProd object that can be used for tests.
    """
    sample_device_role_prod = DeviceRoleProd.objects.create(name="test")
    return sample_device_role_prod


@pytest.mark.django_db
@pytest.fixture(scope="function")
def sample_administration_group(sample_device_role_prod):
    """
    Creates a AdministrationGroup object that can be used for tests.
    """
    sample_administration_group = AdministrationGroup.objects.create(name="test")
    sample_administration_group.DeviceRoleProd.set([sample_device_role_prod])
    sample_administration_group.save()
    return sample_administration_group


@pytest.mark.django_db
@pytest.fixture(scope="function")
def sample_object(sample_device_role_prod, sample_administration_group):
    """
    Creates a Device object that can be used for tests.
    """
    test_domain = DNSDomain.objects.create(name="test.com")

    data = {
       "asset_id": "None",
       "vlan": 100,
       "dns_domain": test_domain,
       "administration_group": sample_administration_group,
       "appl_NAC_DeviceRoleProd": sample_device_role_prod,
       "appl_NAC_Hostname": "test_hostname",
       "appl_NAC_Active": True,
       "appl_NAC_ForceDot1X": False,
       "appl_NAC_Install": True,
       "appl_NAC_AllowAccessCAB": True,
       "appl_NAC_AllowAccessAIR": True,
       "appl_NAC_AllowAccessVPN": False,
       "appl_NAC_AllowAccessCEL": True,
       "appl_NAC_macAddressAIR": None,
       "appl_NAC_macAddressCAB": None,
       "appl_NAC_Certificate": None,
       "synchronized": False,
       "additional_info": "Placeholder"
    }
    return Device.objects.create(**data)
