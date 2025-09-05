import pytest
from django.test import RequestFactory
from django.urls import reverse_lazy
from nac.models import Device, AdministrationGroup, CustomUser
from django.contrib.auth.models import Permission
from tests.test_models.test_device import deviceObject

@pytest.mark.django_db
def test_flags(deviceObject, client):
    deviceObject.synchronized = True
    deviceObject.save()

    perm_delete = Permission.objects.get(codename='delete_device')
    test_user = CustomUser.objects.create()
    test_user.set_password("test")
    test_user.administration_group.set([AdministrationGroup.objects.get(pk=1)])
    test_user.user_permissions.add(perm_delete)
    test_user.save()

    client.force_login(test_user)

    response = client.post(reverse_lazy('device_delete', args=(deviceObject.id,)))
    deviceObject.refresh_from_db()
    assert deviceObject.synchronized is False and deviceObject.deleted is True
