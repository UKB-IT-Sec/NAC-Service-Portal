import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_get_absolute_url(sample_object):
    assert reverse("device_detail", kwargs={"pk": sample_object.pk}) == sample_object.get_absolute_url()


@pytest.mark.django_db
def test_get_appl_NAC_macAddressAIR(sample_object):
    assert sample_object.get_appl_NAC_macAddressAIR() is None


@pytest.mark.django_db
def test_get_appl_NAC_macAddressCAB(sample_object):
    assert sample_object.get_appl_NAC_macAddressCAB() is None
