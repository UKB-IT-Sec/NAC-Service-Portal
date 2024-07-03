import pytest
from nac.models import Device, Area, CustomUser
from nac.views import DeviceListView
from django.test import RequestFactory
from django.urls import reverse_lazy
from pytest_django.asserts import assertQuerysetEqual


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
    test_user.area.set([Area.objects.get(pk=1)])

    request = RequestFactory().get(reverse_lazy("devices") + "?q=" + query)
    request.user = test_user
    view = DeviceListView()
    view.request = request
    result_qs = view.get_queryset()
    print(result_qs)

    assertQuerysetEqual(desired_qs, result_qs, ordered=False)
