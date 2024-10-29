import pytest
from nac.forms import DeviceForm
from nac.models import AuthorizationGroup, DeviceRoleProd, DeviceRoleInst


@pytest.mark.django_db
@pytest.mark.parametrize("appl_NAC_ForceDot1X, appl_NAC_AllowAccessVPN, appl_NAC_Certificate, appl_NAC_AllowAccessAIR, "
                         "appl_NAC_macAddressAIR, appl_NAC_AllowAccessCAB, appl_NAC_macAddressCAB, validity",
                         [(True, True, "test", True, "001132334455", True, "001132334455", True),
                          (True, True, None, True, "001142334455", True, "001142334455", False),
                          (True, True, "test", True, None, True, "001152334455", False),
                          (True, True, "test", True, "001162334455", True, None, False),
                          (False, True, None, True, "001172334455", True, "001172334455", False),
                          (True, False, None, True, "001182334455", True, "001182334455", False),
                          (False, False, None, True, "001192334455", True, "001192334455", True),
                          (True, True, "test", False, None, True, "001123334455", True),
                          (True, True, "test", True, "001122434455", False, None, True)])
def test_clean(appl_NAC_ForceDot1X, appl_NAC_AllowAccessVPN, appl_NAC_Certificate, appl_NAC_AllowAccessAIR,
               appl_NAC_macAddressAIR, appl_NAC_AllowAccessCAB, appl_NAC_macAddressCAB, validity):
    test_DeviceRoleProd = DeviceRoleProd.objects.create(name="test")
    test_DeviceRoleInst = DeviceRoleInst.objects.create(name="test2")
    test_authorization_group = AuthorizationGroup.objects.create(name="test")
    test_authorization_group.DeviceRoleProd.set([test_DeviceRoleProd])
    test_authorization_group.DeviceRoleInst.set([test_DeviceRoleInst])
    form = DeviceForm(data={
       "name": "test",
       "authorization_group": test_authorization_group,
       "appl_NAC_DeviceRoleProd": test_DeviceRoleProd,
       "appl_NAC_FQDN": "test",
       "appl_NAC_Hostname": "test",
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
    })
    assert form.is_valid() is validity
