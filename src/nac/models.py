from django.db import models
from django.contrib.auth.models import User


class Device(models.Model):
    name = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name[:50]