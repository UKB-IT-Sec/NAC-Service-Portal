from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, Device, AuthorizationGroup, DeviceRoleProd
from django import forms
from django.forms import ModelForm, CheckboxInput
from dal import autocomplete
from .validation import normalize_mac, validate_mac
from django.core.exceptions import ValidationError


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = CustomUser
        fields = ("username", "email", "authorization_group",)


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = UserChangeForm.Meta.fields


class DeviceSearchForm(forms.Form):
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(DeviceSearchForm, self).__init__(*args, **kwargs)

        self.fields['authorization_group'] = forms.ModelChoiceField(AuthorizationGroup.objects.filter(
            id__in=user.authorization_group.all()), required=False, label="Authorization Group")

    search_string = forms.CharField(
        label="Search for name, FQDN, hostname or MAC address:", max_length=100, required=False)
    device_role_prod = forms.ModelChoiceField(DeviceRoleProd.objects.all(),
                                              required=False, label="Device Role Prod:")


class DeviceForm(ModelForm):
    class Meta:
        model = Device
        fields = ["asset_id",
                  "appl_NAC_Hostname",
                  "dns_domain",
                  "vlan",
                  "authorization_group",
                  "appl_NAC_DeviceRoleProd",
                  "appl_NAC_DeviceRoleInst",
                  "appl_NAC_Active",
                  "appl_NAC_ForceDot1X",
                  "appl_NAC_Install",
                  "appl_NAC_AllowAccessCAB",
                  "appl_NAC_AllowAccessAIR",
                  "appl_NAC_AllowAccessVPN",
                  "appl_NAC_AllowAccessCEL",
                  "appl_NAC_macAddressAIR",
                  "appl_NAC_macAddressCAB",
                  "synchronized",
                  ]

        widgets = {"dns_domain": autocomplete.ModelSelect2(url="dns_domain-autocomplete"),
                   "authorization_group": autocomplete.ModelSelect2(url="authorization-group-autocomplete"),
                   "appl_NAC_DeviceRoleProd": autocomplete.ModelSelect2(url="DeviceRoleProd-autocomplete", forward=["authorization_group"], ),
                   "appl_NAC_DeviceRoleInst": autocomplete.ModelSelect2(url="DeviceRoleInst-autocomplete", forward=["authorization_group"], ),
                   "appl_NAC_Active": CheckboxInput,
                   "appl_NAC_ForceDot1X": CheckboxInput,
                   "appl_NAC_Install": CheckboxInput,
                   "appl_NAC_AllowAccessCAB": CheckboxInput,
                   "appl_NAC_AllowAccessAIR": CheckboxInput,
                   "appl_NAC_AllowAccessVPN": CheckboxInput,
                   "appl_NAC_AllowAccessCEL": CheckboxInput,
                   "synchronized": forms.HiddenInput(),
                   }

    def clean(self):
        cleaned_data = super().clean()
        dependencies = {"appl_NAC_AllowAccessAIR": "appl_NAC_macAddressAIR",
                        "appl_NAC_AllowAccessCAB": "appl_NAC_macAddressCAB",
                        }

        for field in dependencies:
            if cleaned_data.get(field) and not cleaned_data.get(dependencies[field]):
                self.add_error(dependencies[field],
                               ValidationError("This field cannot be empty while %(field)s is selected",
                                               params={"field": field}))
        # prefill asset_id if not set
        if not cleaned_data.get('asset_id') and cleaned_data.get('appl_NAC_Hostname') and cleaned_data.get('dns_domain'):
            cleaned_data['asset_id'] = f"FQDN_{cleaned_data.get('appl_NAC_Hostname')}.{cleaned_data.get('dns_domain')}"

    def clean_appl_NAC_macAddressAIR(self):
        data = self.cleaned_data["appl_NAC_macAddressAIR"]
        if data:
            mac = normalize_mac(data)
            validate_mac(mac)
        else:
            mac = None
        return mac

    def clean_appl_NAC_Hostname(self):
        hostname = self.cleaned_data.get("appl_NAC_Hostname")
        if "." in hostname:
            raise ValidationError("Hostname contains invalid character")
        return hostname

    def clean_appl_NAC_macAddressCAB(self):
        data = self.cleaned_data["appl_NAC_macAddressCAB"]
        if data:
            data = data.split(",")
            macs = list()
            for item in data:
                mac = normalize_mac(item)
                validate_mac(mac)
                macs.append(mac)
            macs = ",".join(macs)
        else:
            macs = None
        return macs

    def clean_synchronized(self):
        return False
