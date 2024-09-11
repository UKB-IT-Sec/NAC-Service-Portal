from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse


class DeviceRoleProd(models.Model):
    name = models.TextField()

    def __str__(self):
        return self.name[:50]


class DeviceRoleInst(models.Model):
    name = models.TextField()

    def __str__(self):
        return self.name[:50]


class Area(models.Model):
    name = models.TextField()
    DeviceRoleProd = models.ManyToManyField(DeviceRoleProd)
    DeviceRoleInst = models.ManyToManyField(DeviceRoleInst)

    def __str__(self):
        return self.name[:50]


class CustomUser(AbstractUser):
    name = models.TextField()
    area = models.ManyToManyField(Area)


class Device(models.Model):
    name = models.CharField(max_length=100)
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True)
    appl_NAC_DeviceRoleProd = models.ForeignKey(
        DeviceRoleProd, on_delete=models.SET_NULL, null=True)
    appl_NAC_DeviceRoleInst = models.ForeignKey(
        DeviceRoleInst, on_delete=models.SET_NULL, null=True)
    synchronized = models.BooleanField(null=True, default=False)

    appl_NAC_FQDN = models.CharField(null=True, max_length=100)
    appl_NAC_Hostname = models.CharField(null=True, max_length=100)
    appl_NAC_Active = models.BooleanField(null=True, default=True)
    appl_NAC_ForceDot1X = models.BooleanField(null=True, default=True)
    appl_NAC_Install = models.BooleanField(null=True)
    appl_NAC_AllowAccessCAB = models.BooleanField(null=True, default=True)
    appl_NAC_AllowAccessAIR = models.BooleanField(null=True)
    appl_NAC_AllowAccessVPN = models.BooleanField(null=True)
    appl_NAC_AllowAccessCEL = models.BooleanField(null=True)
    appl_NAC_macAddressCAB = models.TextField(null=True, blank=True)
    appl_NAC_macAddressAIR = models.CharField(null=True,
                                              max_length=100, blank=True)
    appl_NAC_Certificate = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name[:50]

    def get_absolute_url(self):
        return reverse("device_detail", kwargs={"pk": self.pk})

    def format_mac(self, mac):
        return ":".join(mac[i:i+2] for i in range(0, 12, 2))

    def get_appl_NAC_macAddressAIR(self):
        if not self.appl_NAC_macAddressAIR:
            return None
        return [self.format_mac(self.appl_NAC_macAddressAIR)]

    def get_appl_NAC_macAddressCAB(self):
        if not self.appl_NAC_macAddressCAB:
            return None
        return [self.format_mac(mac) for mac in
                self.appl_NAC_macAddressCAB.split(",")]
