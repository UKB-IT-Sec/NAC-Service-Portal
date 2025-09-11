import pytest
from django.urls import reverse_lazy


@pytest.mark.django_db
def test_flags(sample_device, logged_in_client):
    sample_device.synchronized = True
    sample_device.deleted = False
    sample_device.save()

    logged_in_client.post(reverse_lazy('device_delete', args=(sample_device.id,)))
    sample_device.refresh_from_db()
    assert sample_device.synchronized is False and sample_device.deleted is True
