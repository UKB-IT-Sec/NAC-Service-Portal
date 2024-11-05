import pytest
from django.test import RequestFactory
from django.core.cache import cache
from unittest.mock import patch
from nac.views import ArmisView


@pytest.fixture
def armis_view():
    return ArmisView()


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.mark.django_db
class TestArmisView:

    @patch('nac.views.get_armis_sites')
    def test_get_context(self, mock_get_armis_sites, armis_view):
        mock_sites = {'1': {'name': 'Site1'}, '2': {'name': 'Site2'}}
        mock_get_armis_sites.return_value = mock_sites

        cache.clear()  # Setup empty Cache
        context = armis_view._get_context()
        assert context['armis_sites'] == mock_sites
        mock_get_armis_sites.assert_called_once()

        mock_get_armis_sites.reset_mock()
        context = armis_view._get_context()
        assert context['armis_sites'] == mock_sites
        mock_get_armis_sites.assert_not_called()  # Shouldnt be called because Cache isnt empty anymore

    @patch('nac.views.ArmisView._get_context')
    @patch('nac.views.render')
    def test_get(self, mock_render, mock_get_context, armis_view, rf):
        mock_context = {'armis_sites': {'1': {'name': 'Site1'}}}
        mock_get_context.return_value = mock_context

        request = rf.get('/armis/')
        armis_view.get(request)

        mock_render.assert_called_once_with(request, armis_view.template_name, mock_context)

    @patch('nac.views.ArmisView._get_context')
    @patch('nac.views.get_devices')
    @patch('nac.views.render')
    def test_post_with_site(self, mock_render, mock_get_devices, mock_get_context, armis_view, rf):
        mock_context = {'armis_sites': {'1': {'name': 'Site1'}}}
        mock_get_context.return_value = mock_context
        mock_devices = [{'name': 'Device1'}, {'name': 'Device2'}]
        mock_get_devices.return_value = mock_devices

        request = rf.post('/armis/', {'site-id': '1'})
        armis_view.post(request)

        expected_context = {
            'armis_sites': {'1': {'name': 'Site1'}},
            'selected_site': '1',
            'devices': mock_devices
        }
        mock_render.assert_called_once_with(request, armis_view.template_name, expected_context)
        mock_get_devices.assert_called_once_with({'name': 'Site1'})

    @patch('nac.views.ArmisView._get_context')
    @patch('nac.views.render')
    def test_post_without_site(self, mock_render, mock_get_context, armis_view, rf):
        mock_context = {'armis_sites': {'1': {'name': 'Site1'}}}
        mock_get_context.return_value = mock_context

        request = rf.post('/armis/')
        armis_view.post(request)

        expected_context = {
            'armis_sites': {'1': {'name': 'Site1'}},
            'selected_site': ''
        }
        mock_render.assert_called_once_with(request, armis_view.template_name, expected_context)
