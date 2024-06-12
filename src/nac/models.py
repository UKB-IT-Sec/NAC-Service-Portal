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
    name = models.TextField()
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True)
    security_group = models.ForeignKey(SecurityGroup, on_delete=models.SET_NULL, null=True)

    appl_NAC_FQDN = models.TextField(null=True) #FQDN
    appl_NAC_Hostname = models.TextField(null=True) #hostname
    appl_NAC_Active = models.BooleanField(null=True)
    appl_NAC_ForceDot1X = models.BooleanField(null=True)
    appl_NAC_Install = models.BooleanField(null=True)
    appl_NAC_AllowAccessCAB = models.BooleanField(null=True)
    appl_NAC_AllowAccessAIR = models.BooleanField(null=True)
    appl_NAC_AllowAccessVPN = models.BooleanField(null=True)
    appl_NAC_AllowAccessCEL = models.BooleanField(null=True)
    appl_NAC_DeviceRoleProd = models.TextField(null=True) #R_ppp
    appl_NAC_DeviceRoleInst = models.TextField(null=True) #R_iii
    appl_NAC_macAddressAIR = models.TextField(null=True) #aabbccddeeff
    appl_NAC_Certificate = models.TextField(null=True) #<>


    def __str__(self):
        return self.name[:50]

    def get_absolute_url(self):
        return reverse("device_detail", kwargs={"pk": self.pk})


class MacAddressCAB(models.Model):
    mac_address = models.TextField()
    device = models.ForeignKey(Device, on_delete=models.CASCADE)



