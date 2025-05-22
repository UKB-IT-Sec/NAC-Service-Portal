import pytest
from unittest.mock import patch
from nac.forms import DeviceForm, MacAddressFormat
from nac.models import AdministrationGroup, DeviceRoleProd, DNSDomain


@pytest.mark.django_db
@pytest.mark.parametrize("appl_NAC_ForceDot1X, appl_NAC_AllowAccessVPN, appl_NAC_Certificate, appl_NAC_AllowAccessAIR, "
                         "appl_NAC_macAddressAIR, appl_NAC_AllowAccessCAB, appl_NAC_macAddressCAB, test_hostname, validity",
                         [(True, True, "test", True, "001132334455", True, "001132334455", "device_1", True),
                          (True, True, None, True, "001142334455", True, "001142334455", "device_1", True),
                          (True, True, "test", True, None, True, "001152334455", "device_1", False),
                          (True, True, "test", True, "001162334455", True, None, "device_1", False),
                          (False, False, None, True, "001192334455", True, "001192334455", "device_1", True),
                          (True, True, "test", False, None, True, "001123334455", "device_1", True),
                          (True, True, "test", False, None, True, "ZZ1123334455", "device_1", False),
                          (True, True, "test", False, None, True, "001123334455", "device.1", False),
                          (True, True, "test", True, "001122434455", False, None, "device_1", True)])
def test_clean(appl_NAC_ForceDot1X, appl_NAC_AllowAccessVPN, appl_NAC_Certificate, appl_NAC_AllowAccessAIR,
               appl_NAC_macAddressAIR, appl_NAC_AllowAccessCAB, appl_NAC_macAddressCAB, test_hostname, validity):
    test_DeviceRoleProd = DeviceRoleProd.objects.create(name="test")
    test_domain = DNSDomain.objects.create(name="test.com")
    test_administration_group = AdministrationGroup.objects.create(name="test")
    test_administration_group.DeviceRoleProd.set([test_DeviceRoleProd])
    form = DeviceForm(data={
       "asset_id": "None",
       "vlan": 100,
       "dns_domain": test_domain,
       "administration_group": test_administration_group,
       "appl_NAC_DeviceRoleProd": test_DeviceRoleProd,
       "appl_NAC_Hostname": test_hostname,
       "appl_NAC_Active": True,
       "appl_NAC_ForceDot1X": appl_NAC_ForceDot1X,
       "appl_NAC_Install": True,
       "appl_NAC_AllowAccessCAB": appl_NAC_AllowAccessCAB,
       "appl_NAC_AllowAccessAIR": appl_NAC_AllowAccessAIR,
       "appl_NAC_AllowAccessVPN": appl_NAC_AllowAccessVPN,
       "appl_NAC_AllowAccessCEL": True,
       "appl_NAC_macAddressAIR": appl_NAC_macAddressAIR,
       "appl_NAC_macAddressCAB": appl_NAC_macAddressCAB,
       "appl_NAC_Certificate": appl_NAC_Certificate,
       "synchronized": False,
       "additional_info": "Placeholder"
    })
    assert form.is_valid() is validity


@pytest.mark.parametrize(
    "input_value,normalized,expected",
    [
        ("", "", ""),
        (None, None, None),
        ("aa:bb:cc:dd:ee:ff", "AABBCCDDEEFF", "AA:BB:CC:DD:EE:FF"),
        ("AA-BB-CC-DD-EE-FF", "AABBCCDDEEFF", "AA:BB:CC:DD:EE:FF"),
        ("aabbccddeeff", "AABBCCDDEEFF", "AA:BB:CC:DD:EE:FF"),
        (
            "aa:bb:cc:dd:ee:ff, 11:22:33:44:55:66",
            ["AABBCCDDEEFF", "112233445566"],
            "AA:BB:CC:DD:EE:FF\t,\t11:22:33:44:55:66",
        ),
    ]
)
def test_format_value(input_value, normalized, expected):
    mac_format = MacAddressFormat()

    with patch("nac.validation.normalize_mac") as mock_normalize:
        if isinstance(normalized, list):
            mock_normalize.side_effect = normalized  # side_effect returns item for item in the normalized-list for repeating function calls
        else:
            mock_normalize.return_value = normalized

        result = mac_format.format_value(input_value)
        assert result == expected
