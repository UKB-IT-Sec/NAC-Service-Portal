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
    security_group = models.ForeignKey(SecurityGroup, on_delete=models.SET_NULL, null=True)

    appl_NAC_FQDN = models.CharField(null=True, max_length=100) #FQDN
    appl_NAC_Hostname = models.CharField(null=True, max_length=100) #hostname
    appl_NAC_Active = models.BooleanField(null=True, default=True)
    appl_NAC_ForceDot1X = models.BooleanField(null=True, default=True)
    appl_NAC_Install = models.BooleanField(null=True)
    appl_NAC_AllowAccessCAB = models.BooleanField(null=True, default=True)
    appl_NAC_AllowAccessAIR = models.BooleanField(null=True)
    appl_NAC_AllowAccessVPN = models.BooleanField(null=True)
    appl_NAC_AllowAccessCEL = models.BooleanField(null=True)
    appl_NAC_DeviceRoleProd = models.CharField(null=True, blank=True, max_length=100) #R_ppp
    appl_NAC_DeviceRoleInst = models.CharField(null=True, blank=True, max_length=100) #R_iii
    appl_NAC_macAddressCAB = models.TextField(null=True) #aabbccddeeff multi value
    appl_NAC_macAddressAIR = models.CharField(null=True, max_length=100) #aabbccddeeff
    appl_NAC_Certificate = models.TextField(null=True) #<>


    def __str__(self):
        return self.name[:50]

    def get_absolute_url(self):
        return reverse("device_detail", kwargs={"pk": self.pk})




