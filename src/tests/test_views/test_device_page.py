import pytest
from nac.models import Device, AuthorizationGroup, CustomUser
from nac.views import DeviceListView
from django.test import RequestFactory
from django.urls import reverse_lazy
from pytest_django.asserts import assertQuerySetEqual


@pytest.mark.django_db
@pytest.mark.parametrize("query, result",
                         [("", [1, 2, 3, 4, 5]),
                          ("dev1", [1]),
                          ("fqdn", [1, 2]),
                          ("host", [4]),
                          ("000000000000", [2]),
                          ("123456789000", [3]),
                          ("noresult", []),
                          ])
def test_device_search(query, result):
    desired_qs = Device.objects.all().filter(id__in=result)
    print(desired_qs)

    test_user = CustomUser.objects.create(name="test")
    test_user.authorization_group.set([AuthorizationGroup.objects.get(pk=1), AuthorizationGroup.objects.get(pk=2)])

    request = RequestFactory().get(reverse_lazy("devices") + "?q=" + query)
    request.user = test_user
    view = DeviceListView()
    view.request = request
    result_qs = view.get_queryset()
    print(result_qs)

    assertQuerySetEqual(desired_qs, result_qs, ordered=False)


@pytest.mark.django_db
@pytest.mark.parametrize("auth_groups, device_roles_prod, result",
                         [([], [], [1, 2, 3, 4, 5]),
                          ([], [1], [1, 3, 5]),
                          ([], [1, 2], [1, 2, 3, 4, 5]),
                          ([], [2], [2, 4]),
                          ([1], [], [1, 2, 5]),
                          ([1], [1], [1, 5]),
                          ([1, 2], [], [1, 2, 3, 4, 5]),
                          ([1], [2], [2]),
                          ([2], [1], [3]),
                          ([1, 2], [], [1, 2, 3, 4, 5]),
                          ([3], [], []),
                          ])
def test_device_filtering(auth_groups, device_roles_prod, result):
    desired_qs = Device.objects.all().filter(id__in=result)
    print(desired_qs)

    test_user = CustomUser.objects.create(name="test")
    test_user.authorization_group.set([AuthorizationGroup.objects.get(pk=1), AuthorizationGroup.objects.get(pk=2)])

    query = "?search_string="
    for device_role_prod in device_roles_prod:
        query += "&device_role_prod="
        query += str(device_role_prod)
    for auth_group in auth_groups:
        query += "&authorization_group="
        query += str(auth_group)

    print(query)

    request = RequestFactory().get(reverse_lazy("devices") + query)
    request.user = test_user
    view = DeviceListView()
    view.request = request
    result_qs = view.get_queryset()
    print(result_qs)

    assertQuerySetEqual(desired_qs, result_qs, ordered=False)
