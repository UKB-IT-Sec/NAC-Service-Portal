import pytest
from nac.subviews.device_management import DeviceUpdateView
from nac.models import AuthorizationGroup, Device, CustomUser
from django.test import RequestFactory
from django.forms.models import model_to_dict


@pytest.mark.django_db
@pytest.mark.parametrize("hostname",
                         [("dev1-v2"),
                          ("dev1-v3"),
                          ("dev1-v4")])
def test_select_version(hostname):
    device_with_history = Device.objects.get(id=1)
    device_with_history.appl_NAC_Hostname = "dev1-v1"
    device_with_history.save()
    device_with_history.appl_NAC_Hostname = "dev1-v2"
    device_with_history.save()
    device_with_history.appl_NAC_Hostname = "dev1-v3"
    device_with_history.save()
    device_with_history.appl_NAC_Hostname = "dev1-v4"
    device_with_history.save()

    history_entry = device_with_history.history.get(appl_NAC_Hostname=hostname)
    expected_data = model_to_dict(history_entry)

    test_user = CustomUser.objects.create(name="test")
    test_user.authorization_group.set([AuthorizationGroup.objects.get(pk=1), AuthorizationGroup.objects.get(pk=2)])

    rf = RequestFactory()
    url = f"/devices/{device_with_history.pk}/edit/"
    post_data = {
        "select": "1",
        "device_version": history_entry.history_id,
    }
    request = rf.post(url, post_data)
    request.user = test_user
    request.path = url

    view = DeviceUpdateView()
    view.setup(request, pk=device_with_history.pk)
    view.object = view.get_object()
    response = view.post(request, pk=device_with_history.pk)

    assert response.status_code == 200
    form = response.context_data["form"]
    assert form.initial["appl_NAC_Hostname"] == expected_data["appl_NAC_Hostname"]


@pytest.mark.django_db
@pytest.mark.parametrize("hostname",
                         [("dev1-v2"),
                          ("dev1-v3"),
                          ("dev1-v4")])
def test_delete_version(hostname):
    device_with_history = Device.objects.get(id=1)
    device_with_history.appl_NAC_Hostname = "dev1-v1"
    device_with_history.save()
    device_with_history.appl_NAC_Hostname = "dev1-v2"
    device_with_history.save()
    device_with_history.appl_NAC_Hostname = "dev1-v3"
    device_with_history.save()
    device_with_history.appl_NAC_Hostname = "dev1-v4"
    device_with_history.save()

    history_entry = device_with_history.history.all().get(appl_NAC_Hostname=hostname)

    test_user = CustomUser.objects.create(name="test")
    test_user.authorization_group.set([AuthorizationGroup.objects.get(pk=1), AuthorizationGroup.objects.get(pk=2)])

    rf = RequestFactory()
    url = f"/devices/{device_with_history.pk}/edit/"
    post_data = {
        "delete": "1",
        "device_version": history_entry.history_id,
    }
    request = rf.post(url, post_data)
    request.user = test_user
    request.path = url

    view = DeviceUpdateView()
    view.setup(request, pk=device_with_history.pk)
    view.object = view.get_object()
    response = view.post(request, pk=device_with_history.pk)

    assert response.status_code == 302
    assert response["Location"] == url

    assert not device_with_history.history.filter(history_id=history_entry.history_id).exists()


@pytest.mark.django_db
def test_select_none():
    device_with_history = Device.objects.get(id=1)
    device_with_history.appl_NAC_Hostname = "dev1-v1"
    device_with_history.save()

    expected_data = model_to_dict(device_with_history)

    test_user = CustomUser.objects.create(name="test")
    test_user.authorization_group.set([AuthorizationGroup.objects.get(pk=1), AuthorizationGroup.objects.get(pk=2)])

    rf = RequestFactory()
    url = f"/devices/{device_with_history.pk}/edit/"
    post_data = {
        "select": "1",
        "device_version": "",
    }
    request = rf.post(url, post_data)
    request.user = test_user
    request.path = url

    view = DeviceUpdateView()
    view.setup(request, pk=device_with_history.pk)
    view.object = view.get_object()
    response = view.post(request, pk=device_with_history.pk)

    assert response.status_code == 200
    form = response.context_data["form"]
    assert form.initial["appl_NAC_Hostname"] == expected_data["appl_NAC_Hostname"]


@pytest.mark.django_db
def test_delete_none():
    device_with_history = Device.objects.get(id=1)
    device_with_history.appl_NAC_Hostname = "dev1-v1"
    device_with_history.save()

    expected_data = model_to_dict(device_with_history)

    test_user = CustomUser.objects.create(name="test")
    test_user.authorization_group.set([AuthorizationGroup.objects.get(pk=1), AuthorizationGroup.objects.get(pk=2)])

    rf = RequestFactory()
    url = f"/devices/{device_with_history.pk}/edit/"
    post_data = {
        "delete": "1",
        "device_version": "",
    }
    request = rf.post(url, post_data)
    request.user = test_user
    request.path = url

    view = DeviceUpdateView()
    view.setup(request, pk=device_with_history.pk)
    view.object = view.get_object()
    response = view.post(request, pk=device_with_history.pk)

    assert response.status_code == 200
    form = response.context_data["form"]
    assert form.initial["appl_NAC_Hostname"] == expected_data["appl_NAC_Hostname"]
