from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, Device
from django.forms import ModelForm, Field
from dal import autocomplete
from .validation import validate_fqdn, normalize_mac, validate_mac


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = CustomUser
        fields = ("username", "email", "area",)


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = UserChangeForm.Meta.fields


class FQDNField(Field):
    def validate(self, value):
        super().validate(value)
        validate_fqdn(value)


class DeviceForm(ModelForm):
    class Meta:
        model = Device
        fields = ["name",
                  "area",
                  "security_group",
                  "appl_NAC_FQDN",
                  "appl_NAC_Hostname",
                  "appl_NAC_Active",
                  "appl_NAC_ForceDot1X",
                  "appl_NAC_Install",
                  "appl_NAC_AllowAccessCAB",
                  "appl_NAC_AllowAccessAIR",
                  "appl_NAC_AllowAccessVPN",
                  "appl_NAC_AllowAccessCEL",
                  "appl_NAC_DeviceRoleProd",
                  "appl_NAC_DeviceRoleInst",
                  "appl_NAC_macAddressAIR",
                  "appl_NAC_macAddressCAB",
                  "appl_NAC_Certificate", ]

        widgets = {"security_group": autocomplete.ModelSelect2(url="security-group-autocomplete", forward=["area"],),
                   "area": autocomplete.ModelSelect2(url="area-autocomplete"), }

    def clean_appl_NAC_macAddressAIR(self):
        data = self.cleaned_data["appl_NAC_macAddressAIR"]
        mac = normalize_mac(data)
        validate_mac(mac)
        return mac
