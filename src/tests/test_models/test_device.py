import pytest
from django.urls import reverse
from nac.models import AuthorizationGroup, DeviceRoleProd, DeviceRoleInst, DNSDomain, Device


@pytest.mark.django_db
@pytest.fixture
def deviceObject():
    test_DeviceRoleProd = DeviceRoleProd.objects.create(name="test")
    test_DeviceRoleInst = DeviceRoleInst.objects.create(name="test2")
    test_domain = DNSDomain.objects.create(name="test.com")
    test_authorization_group = AuthorizationGroup.objects.create(name="test")
    test_authorization_group.DeviceRoleProd.set([test_DeviceRoleProd])
    test_authorization_group.DeviceRoleInst.set([test_DeviceRoleInst])
    data = {
       "asset_id": "None",
       "vlan": 100,
       "dns_domain": test_domain,
       "authorization_group": test_authorization_group,
       "appl_NAC_DeviceRoleProd": test_DeviceRoleProd,
       "appl_NAC_Hostname": "test_hostname",
       "appl_NAC_Active": True,
       "appl_NAC_ForceDot1X": False,
       "appl_NAC_Install": True,
       "appl_NAC_AllowAccessCAB": True,
       "appl_NAC_AllowAccessAIR": True,
       "appl_NAC_AllowAccessVPN": False,
       "appl_NAC_AllowAccessCEL": True,
       "appl_NAC_DeviceRoleInst": test_DeviceRoleInst,
       "appl_NAC_macAddressAIR": None,
       "appl_NAC_macAddressCAB": None,
       "appl_NAC_Certificate": None,
       "synchronized": False,
       "additional_info": "Placeholder"
    }
    return Device.objects.create(**data)


@pytest.mark.django_db
def test_get_absolute_url(deviceObject):
    assert reverse("device_detail", kwargs={"pk": deviceObject.pk}) == deviceObject.get_absolute_url()


@pytest.mark.django_db
def test_get_appl_NAC_macAddressAIR(deviceObject):
    assert deviceObject.get_appl_NAC_macAddressAIR() is None


@pytest.mark.django_db
def test_get_appl_NAC_macAddressCAB(deviceObject):
    assert deviceObject.get_appl_NAC_macAddressCAB() is None
