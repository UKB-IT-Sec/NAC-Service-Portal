import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_get_absolute_url(sample_device):
    assert reverse("device_detail", kwargs={"pk": sample_device.pk}) == sample_device.get_absolute_url()


@pytest.mark.django_db
def test_get_appl_NAC_macAddressAIR(sample_device):
    assert sample_device.get_appl_NAC_macAddressAIR() is None


@pytest.mark.django_db
def test_get_appl_NAC_macAddressCAB(sample_device):
    assert sample_device.get_appl_NAC_macAddressCAB() is None
