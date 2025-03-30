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


class DNSDomain(models.Model):
    name = models.TextField()

    def __str__(self):
        return self.name[:50]


class AuthorizationGroup(models.Model):
    name = models.TextField()
    DeviceRoleProd = models.ManyToManyField(DeviceRoleProd)
    DeviceRoleInst = models.ManyToManyField(DeviceRoleInst)

    def __str__(self):
        return self.name[:50]


class CustomUser(AbstractUser):
    name = models.TextField()
    authorization_group = models.ManyToManyField(AuthorizationGroup)


class Device(models.Model):
    asset_id = models.CharField(null=True, blank=True, max_length=150)
    authorization_group = models.ForeignKey(AuthorizationGroup, on_delete=models.SET_NULL, null=True)
    appl_NAC_DeviceRoleProd = models.ForeignKey(
        DeviceRoleProd, on_delete=models.SET_NULL, null=True)
    appl_NAC_DeviceRoleInst = models.ForeignKey(
        DeviceRoleInst, on_delete=models.SET_NULL, null=True)
    synchronized = models.BooleanField(null=True, default=False)

    dns_domain = models.ForeignKey(DNSDomain, on_delete=models.SET_NULL, null=True)
    vlan = models.CharField(null=True, blank=True,  max_length=100)
    additional_info = models.TextField(null=True, blank=True)
    appl_NAC_Hostname = models.CharField(null=True, max_length=100)
    appl_NAC_Active = models.BooleanField(null=True, default=True)
    appl_NAC_ForceDot1X = models.BooleanField(null=True, default=True)
    appl_NAC_Install = models.BooleanField(null=True)
    appl_NAC_AllowAccessCAB = models.BooleanField(null=True, default=True)
    appl_NAC_AllowAccessAIR = models.BooleanField(null=True)
    appl_NAC_AllowAccessVPN = models.BooleanField(null=True)
    appl_NAC_AllowAccessCEL = models.BooleanField(null=True)
    appl_NAC_macAddressCAB = models.TextField(null=True,
                                              blank=True, unique=True)
    appl_NAC_macAddressAIR = models.TextField(null=True,
                                              blank=True, unique=True)
    appl_NAC_Certificate = models.TextField(null=True, blank=True)

    @property
    def appl_NAC_FQDN(self):
        return f'{self.appl_NAC_Hostname}.{self.dns_domain}'

    def save(self, *args, **kwargs):
        if not self.asset_id:
            self.asset_id = f"FQDN_{self.appl_NAC_FQDN}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.appl_NAC_Hostname[:100]

    def get_absolute_url(self):
        return reverse("device_detail", kwargs={"pk": self.pk})

    def format_mac(self, mac):
        mac = mac.upper()
        return ":".join(mac[i:i+2] for i in range(0, 12, 2))

    def get_appl_NAC_macAddressAIR(self):
        if not self.appl_NAC_macAddressAIR:
            return None
        return [self.format_mac(mac) for mac in
                self.appl_NAC_macAddressAIR.split(",")]

    def get_appl_NAC_macAddressCAB(self):
        if not self.appl_NAC_macAddressCAB:
            return None
        return [self.format_mac(mac) for mac in
                self.appl_NAC_macAddressCAB.split(",")]
