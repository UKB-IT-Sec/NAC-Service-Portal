import pytest
from nac.forms import DeviceForm
from nac.models import Area, DeviceRoleProd


@pytest.mark.django_db
@pytest.mark.parametrize("appl_NAC_ForceDot1X, appl_NAC_AllowAccessVPN, appl_NAC_Certificate, appl_NAC_AllowAccessAIR, "
                         "appl_NAC_macAddressAIR, appl_NAC_AllowAccessCAB, appl_NAC_macAddressCAB, validity",
                         [(True, True, "test", True, "001122334455", True, "001122334455", True),
                          (True, True, None, True, "001122334455", True, "001122334455", False),
                          (True, True, "test", True, None, True, "001122334455", False),
                          (True, True, "test", True, "001122334455", True, None, False),
                          (False, True, None, True, "001122334455", True, "001122334455", False),
                          (True, False, None, True, "001122334455", True, "001122334455", False),
                          (False, False, None, True, "001122334455", True, "001122334455", True),
                          (True, True, "test", False, None, True, "001122334455", True),
                          (True, True, "test", True, "001122334455", False, None, True)])
def test_clean(appl_NAC_ForceDot1X, appl_NAC_AllowAccessVPN, appl_NAC_Certificate, appl_NAC_AllowAccessAIR,
               appl_NAC_macAddressAIR, appl_NAC_AllowAccessCAB, appl_NAC_macAddressCAB, validity):
    test_DeviceRoleProd = DeviceRoleProd.objects.create(name="test")
    test_area = Area.objects.create(name="test")
    test_area.DeviceRoleProd.set([test_DeviceRoleProd])
    form = DeviceForm(data={
       "name": "test",
       "area": test_area,
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
       "appl_NAC_DeviceRoleInst": "test",
       "appl_NAC_macAddressAIR": appl_NAC_macAddressAIR,
       "appl_NAC_macAddressCAB": appl_NAC_macAddressCAB,
       "appl_NAC_Certificate": appl_NAC_Certificate,
       "synchronized": False,
    })

    assert form.is_valid() is validity
