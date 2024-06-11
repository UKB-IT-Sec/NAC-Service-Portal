from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, Device
from django.forms import ModelForm
from dal import autocomplete

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = CustomUser
        fields = ("username", "email", "area",)


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = UserChangeForm.Meta.fields


class DeviceForm(ModelForm):
    class Meta:
        model = Device
        fields = ["name", "area", "security_group", ]
        widgets = {"security_group": autocomplete.ModelSelect2(url="security-group-autocomplete", forward=["area"],),
                   "area": autocomplete.ModelSelect2(url="area-autocomplete"), }