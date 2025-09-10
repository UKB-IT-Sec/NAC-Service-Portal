import pytest
from django.urls import reverse_lazy
from nac.models import AdministrationGroup, CustomUser
from django.contrib.auth.models import Permission


@pytest.mark.django_db
def test_flags(sample_device, client):
    sample_device.synchronized = True
    sample_device.deleted = False
    sample_device.save()

    perm_delete = Permission.objects.get(codename='delete_device')
    test_user = CustomUser.objects.create()
    test_user.set_password("test")
    test_user.administration_group.set([AdministrationGroup.objects.get(pk=1)])
    test_user.user_permissions.add(perm_delete)
    test_user.save()

    client.force_login(test_user)

    client.post(reverse_lazy('device_delete', args=(sample_device.id,)))
    sample_device.refresh_from_db()
    assert sample_device.synchronized is False and sample_device.deleted is True
