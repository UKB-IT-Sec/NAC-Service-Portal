import pytest
from nac.forms import DeviceForm
from nac.models import AuthorizationGroup, DeviceRoleProd, DeviceRoleInst, DNSDomain


@pytest.mark.django_db
@pytest.mark.parametrize("appl_NAC_ForceDot1X, appl_NAC_AllowAccessVPN, appl_NAC_Certificate, appl_NAC_AllowAccessAIR, "
                         "appl_NAC_macAddressAIR, appl_NAC_AllowAccessCAB, appl_NAC_macAddressCAB, test_hostname, validity",
                         [(True, True, "test", True, "001132334455", True, "001132334455", "device_1", True),
                          (True, True, None, True, "001142334455", True, "001142334455", "device_1", True),
                          (True, True, "test", True, None, True, "001152334455", "device_1", False),
                          (True, True, "test", True, "001162334455", True, None, "device_1", False),
                          (False, False, None, True, "001192334455", True, "001192334455", "device_1", True),
                          (True, True, "test", False, None, True, "001123334455", "device_1", True),
                          (True, True, "test", False, None, True, "001123334455", "device.1", False),
                          (True, True, "test", True, "001122434455", False, None, "device_1", True)])
def test_clean(appl_NAC_ForceDot1X, appl_NAC_AllowAccessVPN, appl_NAC_Certificate, appl_NAC_AllowAccessAIR,
               appl_NAC_macAddressAIR, appl_NAC_AllowAccessCAB, appl_NAC_macAddressCAB, test_hostname, validity):
    test_DeviceRoleProd = DeviceRoleProd.objects.create(name="test")
    test_DeviceRoleInst = DeviceRoleInst.objects.create(name="test2")
    test_domain = DNSDomain.objects.create(name="test.com")
    test_authorization_group = AuthorizationGroup.objects.create(name="test")
    test_authorization_group.DeviceRoleProd.set([test_DeviceRoleProd])
    test_authorization_group.DeviceRoleInst.set([test_DeviceRoleInst])
    form = DeviceForm(data={
       "asset_id": "None",
       "vlan": 100,
       "dns_domain": test_domain,
       "authorization_group": test_authorization_group,
       "appl_NAC_DeviceRoleProd": test_DeviceRoleProd,
       "appl_NAC_FQDN": "test",
       "appl_NAC_Hostname": test_hostname,
       "appl_NAC_Active": True,
       "appl_NAC_ForceDot1X": appl_NAC_ForceDot1X,
       "appl_NAC_Install": True,
       "appl_NAC_AllowAccessCAB": appl_NAC_AllowAccessCAB,
       "appl_NAC_AllowAccessAIR": appl_NAC_AllowAccessAIR,
       "appl_NAC_AllowAccessVPN": appl_NAC_AllowAccessVPN,
       "appl_NAC_AllowAccessCEL": True,
       "appl_NAC_DeviceRoleInst": test_DeviceRoleInst,
       "appl_NAC_macAddressAIR": appl_NAC_macAddressAIR,
       "appl_NAC_macAddressCAB": appl_NAC_macAddressCAB,
       "appl_NAC_Certificate": appl_NAC_Certificate,
       "synchronized": False,
       "additional_info": "Placeholder"
    })
    assert form.is_valid() is validity
