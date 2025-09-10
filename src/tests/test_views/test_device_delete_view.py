import pytest
from django.urls import reverse_lazy


@pytest.mark.django_db
def test_flags(sample_device, sample_user, client):
    sample_device.synchronized = True
    sample_device.deleted = False
    sample_device.save()

    client.force_login(sample_user)

    client.post(reverse_lazy('device_delete', args=(sample_device.id,)))
    sample_device.refresh_from_db()
    assert sample_device.synchronized is False and sample_device.deleted is True
