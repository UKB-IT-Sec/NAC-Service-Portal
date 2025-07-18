import pytest
from nac.models import Device, AdministrationGroup, CustomUser
from django.contrib.auth.models import Group, Permission
from nac.subviews.device_management import DeviceListView
from django.test import RequestFactory
from django.urls import reverse_lazy
from pytest_django.asserts import assertQuerySetEqual


@pytest.mark.django_db
@pytest.mark.parametrize("query, result",
                         [("", [1, 2, 3, 4, 5]),
                          ("dev1", [1]),
                          ("host", [4]),
                          ("000000000000", [2]),
                          ("123456789000", [3]),
                          ("noresult", []),
                          ])
def test_device_search(query, result):
    desired_qs = Device.objects.all().filter(id__in=result)

    test_user = CustomUser.objects.create()
    test_user.administration_group.set([AdministrationGroup.objects.get(pk=1), AdministrationGroup.objects.get(pk=2)])

    request = RequestFactory().get(reverse_lazy("devices") + "?search_string=" + query)
    request.user = test_user
    view = DeviceListView()
    view.request = request
    result_qs = view.get_queryset()

    assertQuerySetEqual(desired_qs, result_qs, ordered=False)


@pytest.mark.django_db
def test_result_rendering(client):
    test_group = Group.objects.create(name='view')
    perm_view = Permission.objects.get(codename='view_device')
    test_group.permissions.add(perm_view)

    test_user = CustomUser.objects.create()
    test_user.set_password("test")
    test_user.administration_group.set([AdministrationGroup.objects.get(pk=1)])
    test_user.groups.add(test_group)
    test_user.save()

    client.force_login(test_user)

    url = reverse_lazy('devices')
    response = client.get(url)
    assert response.status_code == 200

    ajax_response = client.get(
        url,  # The URL where the AJAX request is sent
        {"search_string": "", "administration_group": "", "device_role_prod": ""},  # Parameters to be sent in the AJAX request
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'  # Indicate it's an AJAX request
    )

    assert ajax_response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("admin_group, device_role_prod, result",
                         [("", "", [1, 2, 3, 4, 5]),
                          ("", 1, [1, 3, 5]),
                          ("", 2, [2, 4]),
                          (1, "", [1, 2, 5]),
                          (1, 1, [1, 5]),
                          (1, 2, [2]),
                          (2, 1, [3]),
                          (3, "", []),
                          ])
def test_device_filtering(admin_group, device_role_prod, result):
    desired_qs = Device.objects.all().filter(id__in=result)
    print(desired_qs)

    test_user = CustomUser.objects.create()
    test_user.administration_group.set([AdministrationGroup.objects.get(pk=1), AdministrationGroup.objects.get(pk=2)])

    query = "?search_string="
    query += "&device_role_prod="
    query += str(device_role_prod)
    query += "&administration_group="
    query += str(admin_group)

    request = RequestFactory().get(reverse_lazy("devices") + query)
    request.user = test_user
    view = DeviceListView()
    view.request = request
    result_qs = view.get_queryset()
    print(result_qs)

    assertQuerySetEqual(desired_qs, result_qs, ordered=False)


@pytest.mark.django_db
def test_csv_export_view(client):
    test_user = CustomUser.objects.create()
    test_user.set_password("test")
    test_user.administration_group.set([AdministrationGroup.objects.get(pk=1)])
    test_user.user_permissions.add(Permission.objects.get(codename='view_device'))
    test_user.save()
    client.force_login(test_user)

    url = reverse_lazy('device_export_csv')
    response = client.get(url)
    assert response.status_code == 200
