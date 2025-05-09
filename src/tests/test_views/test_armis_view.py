import pytest
from django.test import RequestFactory
from django.core.cache import cache
from unittest.mock import patch
from nac.subviews.armis import ArmisView


@pytest.fixture
def armis_view():
    return ArmisView()


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.mark.django_db
class TestArmisView:

    @patch('nac.subviews.armis.get_armis_sites')
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

    @patch('nac.subviews.armis.ArmisView._get_context')
    @patch('nac.subviews.armis.render')
    def test_get(self, mock_render, mock_get_context, armis_view, rf):
        mock_context = {'armis_sites': {'1': {'name': 'Site1'}}}
        mock_get_context.return_value = mock_context

        request = rf.get('/armis/')
        armis_view.get(request)

        mock_render.assert_called_once_with(request, armis_view.template_name, mock_context)

    @patch('nac.subviews.armis.ArmisView._get_context')
    @patch('nac.subviews.armis.get_devices')
    @patch('nac.subviews.armis.render')
    def test_post_with_site(self, mock_render, mock_get_devices, mock_get_context, armis_view, rf):
        mock_context = {'armis_sites': {'1': {'name': 'Site1'}}}
        mock_get_context.return_value = mock_context
        mock_devices = [{'name': 'Device1', 'boundaries': 'boundary1'}, {'name': 'Device2', 'boundaries': 'boundary2'}]
        mock_get_devices.return_value = mock_devices

        request = rf.post('/armis/', {'site-ids[]': '1'})
        armis_view.post(request)

        expected_context = {
            'armis_sites': {'1': {'name': 'Site1'}},
            'display': False,
            'selected_sites': ['1'],
            'devices': mock_devices,
            'boundaries': ['boundary1', 'boundary2']
        }
        mock_render.assert_called_once_with(request, armis_view.template_name, expected_context)
        mock_get_devices.assert_called_once_with(['Site1'])

    @patch('nac.subviews.armis.ArmisView._get_context')
    @patch('nac.subviews.armis.get_single_device')
    @patch('nac.subviews.armis.get_boundaries')
    @patch('nac.subviews.armis.render')
    def test_post_without_site(self, mock_render, mock_get_boundaries, mock_get_single_device, mock_get_context, armis_view, rf):
        mock_context = {'armis_sites': {'1': {'name': 'Site1'}}}
        mock_get_context.return_value = mock_context
        mock_get_single_device.return_value = {'device': 'Default'}
        mock_get_boundaries.return_value = {'boundary'}
        request = rf.post('/armis/')
        armis_view.post(request)

        expected_context = {
            'armis_sites': {'1': {'name': 'Site1'}},
            'display': True,
            'selected_sites': '',
            'devices': {'device': 'Default'},
            'boundaries': {'boundary'}
        }
        mock_render.assert_called_once_with(request, armis_view.template_name, expected_context)
