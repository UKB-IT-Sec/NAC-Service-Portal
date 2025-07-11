from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm
from .models import CustomUser, Device, AdministrationGroup, DeviceRoleProd, DNSDomain
from django import forms
from django.forms import ModelForm, CheckboxInput
from dal import autocomplete
from .validation import normalize_mac, validate_mac
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from crispy_forms.bootstrap import FieldWithButtons
import datetime
from django.utils.timezone import localtime
import re
import magic


class CustomUserCreationForm(AdminUserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email", "administration_group",)


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = UserChangeForm.Meta.fields


class FileUploadSelectForm(forms.Form):
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(FileUploadSelectForm, self).__init__(*args, **kwargs)
        self.fields['administration_group'] = forms.ModelChoiceField(AdministrationGroup.objects.filter(
            id__in=user.administration_group.all()), required=True, label="Administration Group")
        self.fields['dns_domain'] = forms.ModelChoiceField(queryset=DNSDomain.objects.all(), required=True, label="DNS-Domain")


class FileUploadForm(forms.Form):
    file = forms.FileField(
        label="Upload File",
        required=True,
        help_text="Supports only .csv-Format",
        allow_empty_file=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )

    def clean_file(self):
        uploaded_file = self.cleaned_data.get('file')
        if uploaded_file:
            mime = magic.from_buffer(uploaded_file.read(2048), mime=True)
            uploaded_file.seek(0)

            if mime not in ['text/csv', 'text/plain']:
                raise ValidationError("Wrong File-Format (MIME-Type: %s)" % mime)
            from helper.file_integration import validate_header
            if not validate_header(uploaded_file):
                raise ValidationError("Wrong Header-Format")
            uploaded_file.seek(0)
        return uploaded_file


class DeviceSearchForm(forms.Form):

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(DeviceSearchForm, self).__init__(*args, **kwargs)

        self.fields["search_string"] = forms.CharField(
            label="Search for Asset ID, Hostname or MAC Address:", max_length=100, required=False)
        self.fields["device_role_prod"] = forms.ModelChoiceField(DeviceRoleProd.objects.all(),
                                                                 required=False, label="Device Role Prod:")
        self.fields["administration_group"] = forms.ModelChoiceField(AdministrationGroup.objects.filter(
            id__in=user.administration_group.all()), required=False, label="Administration Group")

        self.fields["show_deleted"] = forms.ChoiceField(
            choices=[("present", "Without deleted devices"),
                     ("both", "With deleted devices"),
                     ("deleted", "Only deleted devices")],
            label="Show deleted devices?", required=False)


class MacAddressFormat(forms.Textarea):
    def format_value(self, value):
        if not value:
            return value
        macs = [normalize_mac(mac.strip()) for mac in value.split(",")]
        return '\t,\t'.join(':'.join(mac[i:i+2] for i in range(0, 12, 2)) for mac in macs)


class DeviceForm(ModelForm):
    class Meta:
        model = Device
        fields = ["asset_id",
                  "administration_group",
                  "appl_NAC_Hostname",
                  "dns_domain",
                  "vlan",
                  "appl_NAC_DeviceRoleProd",
                  "appl_NAC_Active",
                  "appl_NAC_ForceDot1X",
                  "appl_NAC_Install",
                  "allowLdapSync",
                  "appl_NAC_AllowAccessCAB",
                  "appl_NAC_AllowAccessAIR",
                  "appl_NAC_AllowAccessVPN",
                  "appl_NAC_AllowAccessCEL",
                  "appl_NAC_macAddressCAB",
                  "appl_NAC_macAddressAIR",
                  "synchronized",
                  "additional_info",
                  "source",
                  "deleted"
                  ]

        widgets = {"dns_domain": autocomplete.ModelSelect2(url="dns_domain-autocomplete"),
                   "administration_group": autocomplete.ModelSelect2(url="administration-group-autocomplete"),
                   "appl_NAC_DeviceRoleProd": autocomplete.ModelSelect2(url="DeviceRoleProd-autocomplete", forward=["administration_group"], ),
                   "appl_NAC_Active": CheckboxInput,
                   "appl_NAC_ForceDot1X": CheckboxInput,
                   "appl_NAC_Install": CheckboxInput,
                   "allowLdapSync": CheckboxInput,
                   "appl_NAC_AllowAccessCAB": CheckboxInput,
                   "appl_NAC_AllowAccessAIR": CheckboxInput,
                   "appl_NAC_AllowAccessVPN": CheckboxInput,
                   "appl_NAC_AllowAccessCEL": CheckboxInput,
                   "appl_NAC_macAddressCAB": MacAddressFormat(),
                   "appl_NAC_macAddressAIR": MacAddressFormat(),
                   "synchronized": forms.HiddenInput(),
                   "deleted": CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
                   }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['source'].widget.attrs['readonly'] = True
        self.fields['vlan'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super().clean()
        dependencies = {"appl_NAC_AllowAccessCAB": "appl_NAC_macAddressCAB",
                        "appl_NAC_AllowAccessAIR": "appl_NAC_macAddressAIR",
                        }

        for field in dependencies:
            if cleaned_data.get(field) and not cleaned_data.get(dependencies[field]):
                self.add_error(dependencies[field],
                               ValidationError("This field cannot be empty while %(field)s is selected",
                                               params={"field": field}))
        # prefill asset_id if not set
        if not cleaned_data.get('asset_id') or cleaned_data.get('asset_id').startswith('FQDN') and cleaned_data.get('appl_NAC_Hostname') and cleaned_data.get('dns_domain'):
            cleaned_data['asset_id'] = f"FQDN_{cleaned_data.get('appl_NAC_Hostname')}.{cleaned_data.get('dns_domain')}"

        administration_group = cleaned_data.get('administration_group')
        device_role_prod = cleaned_data.get('appl_NAC_DeviceRoleProd')

        if administration_group and device_role_prod:
            if not administration_group.DeviceRoleProd.filter(id=device_role_prod.id).exists():
                self.add_error('appl_NAC_DeviceRoleProd', ValidationError(
                        f"Device Role '{device_role_prod}' not in Administration Group '{administration_group}'")
                )
        return cleaned_data

    def clean_appl_NAC_Hostname(self):
        hostname = self.cleaned_data.get("appl_NAC_Hostname")

        if re.search(r'[!"#$%&\'()*+,./:;<=>?@[\\\]^_`{|}~]', hostname):
            raise ValidationError("Hostname contains invalid character")
        return hostname

    def clean_appl_NAC_macAddressCAB(self):
        return self._clean_mac_address('appl_NAC_macAddressCAB')

    def clean_appl_NAC_macAddressAIR(self):
        return self._clean_mac_address('appl_NAC_macAddressAIR')

    def _clean_mac_address(self, field_name):
        data = self.cleaned_data[field_name]
        if data:
            macs = []
            for item in data.split(","):
                mac = normalize_mac(item.strip())
                try:
                    validate_mac(mac)
                except ValidationError:
                    raise
                if mac not in macs:
                    macs.append(mac)
            return ",".join(macs)
        return None

    def clean_synchronized(self):
        return False


class DeviceHistoryForm(forms.Form):
    def __init__(self, device, selected_version, *args, **kwargs):
        super(DeviceHistoryForm, self).__init__(*args, **kwargs)
        n = 3  # number of device versions to be shown in update view
        last_n_device_versions = []

        if device.history.first() is not None:
            last_n_device_versions.append(device.history.first())
            for i in range(n-1):
                if last_n_device_versions[i].prev_record is not None:
                    last_n_device_versions.append(last_n_device_versions[i].prev_record)
                else:
                    break
        else:
            device.save()

        device_version_ids = [version.history_id for version in last_n_device_versions]
        device_version_queryset = device.history.all().filter(history_id__in=device_version_ids)

        self.fields["device_version"] = HistoryModelChoiceField(device_version_queryset,
                                                                required=False,
                                                                label="Select previous version",
                                                                initial=selected_version,
                                                                )
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            FieldWithButtons("device_version", Submit("select", "Select", css_class="ms-2"),
                             Submit("delete", "Delete from history", css_class="btn-secondary ms-2")),

        )


class HistoryModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):           # this makes the options in the dropdown more readable
        version_datetime = obj.history_date
        version_datetime_no_microseconds = datetime.datetime(year=version_datetime.year,
                                                             month=version_datetime.month,
                                                             day=version_datetime.day,
                                                             hour=version_datetime.hour,
                                                             minute=version_datetime.minute,
                                                             second=version_datetime.second,
                                                             microsecond=0,
                                                             tzinfo=version_datetime.tzinfo,)
        return localtime(version_datetime_no_microseconds).isoformat(" ")
