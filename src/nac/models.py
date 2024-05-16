from django.db import models


class Device(models.Model):
    name = models.TextField()

    def __str__(self):
        return self.name[:50]