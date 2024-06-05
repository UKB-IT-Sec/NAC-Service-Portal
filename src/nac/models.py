from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.forms import ModelForm
from dal import autocomplete


class SecurityGroup(models.Model):
    name = models.TextField()

    def __str__(self):
        return self.name[:50]


class Area(models.Model):
    name = models.TextField()
    security_group = models.ManyToManyField(SecurityGroup)

    def __str__(self):
        return self.name[:50]


class CustomUser(AbstractUser):
    name = models.TextField()
    area = models.ManyToManyField(Area)


class Device(models.Model):
    name = models.TextField()
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True)
    security_group = models.ForeignKey(SecurityGroup, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name[:50]

    def get_absolute_url(self):
        return reverse("device_detail", kwargs={"pk": self.pk})


class DeviceForm(ModelForm):
    class Meta:
        model = Device
        fields = ["name", "area", "security_group", ]
        widgets = {"security_group": autocomplete.ModelSelect2(url="security-group-autocomplete", forward=["area"]),
                   "area": autocomplete.ModelSelect2(url="area-autocomplete"), }

