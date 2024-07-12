from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse


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
    name = models.CharField(max_length=100)
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True)
    security_group = models.ForeignKey(SecurityGroup,
                                       on_delete=models.SET_NULL, null=True)
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
    appl_NAC_DeviceRoleProd = models.CharField(null=True,
                                               blank=True, max_length=100)
    appl_NAC_DeviceRoleInst = models.CharField(null=True,
                                               blank=True, max_length=100)
    appl_NAC_macAddressCAB = models.TextField(null=True, blank=True)
    appl_NAC_macAddressAIR = models.CharField(null=True,
                                              max_length=100, blank=True)
    appl_NAC_Certificate = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name[:50]

    def get_absolute_url(self):
        return reverse("device_detail", kwargs={"pk": self.pk})

    def split_MAC(self):
        def format_mac(mac):
            return ":".join(mac[i:i+2] for i in range(0, 12, 2)) \
                if mac else None
        return {
            "appl_NAC_macAddressAIR":
                [format_mac(self.appl_NAC_macAddressAIR)],
            "appl_NAC_macAddressCAB": [format_mac(mac) for mac in
                                       self.appl_NAC_macAddressCAB.split(",")]
        }
