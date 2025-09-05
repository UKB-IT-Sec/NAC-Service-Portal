import pytest
from django.urls import reverse_lazy
from nac.models import AdministrationGroup, CustomUser
from django.contrib.auth.models import Permission


@pytest.mark.django_db
def test_flags(sample_object, client):
    sample_object.synchronized = True
    sample_object.deleted = False
    sample_object.save()

    perm_delete = Permission.objects.get(codename='delete_device')
    test_user = CustomUser.objects.create()
    test_user.set_password("test")
    test_user.administration_group.set([AdministrationGroup.objects.get(pk=1)])
    test_user.user_permissions.add(perm_delete)
    test_user.save()

    client.force_login(test_user)

    client.post(reverse_lazy('device_delete', args=(sample_object.id,)))
    sample_object.refresh_from_db()
    assert sample_object.synchronized is False and sample_object.deleted is True
