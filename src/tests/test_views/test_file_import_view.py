import pytest
import io
from django.urls import reverse
from django.test import Client
from nac.models import CustomUser
from unittest.mock import patch, MagicMock
from helper.file_integration import ESSENTIAL_HEADER


@pytest.fixture
def logged_in_client(db):
    CustomUser.objects.create_user(username="testuser", password="testpass")
    client = Client()
    client.login(username="testuser", password="testpass")
    return client


@pytest.mark.django_db
def test_get_download_template(logged_in_client):
    url = reverse('file_import')
    response = logged_in_client.get(url, {'download_template': '1'})
    assert response.status_code == 200
    assert response['Content-Type'] == 'text/csv'
    assert 'import_schema.csv' in response['Content-Disposition']
    content = response.content.decode()
    assert all(header in content for header in ESSENTIAL_HEADER)


@pytest.mark.django_db
def test_get_initial_form(logged_in_client):
    url = reverse('file_import')
    response = logged_in_client.get(url)
    assert response.status_code == 200
    assert 'form' in response.context
    assert response.context['step'] == 1


@pytest.mark.django_db
@patch("helper.file_integration.get_devices")
@patch("nac.forms.FileUploadForm")
def test_post_step1_valid(mock_form, mock_get_devices, logged_in_client):
    url = reverse('file_import')
    mock_form_instance = MagicMock()
    mock_form_instance.is_valid.return_value = True
    mock_form.return_value = mock_form_instance
    mock_get_devices.return_value = [{'foo': 'bar'}]
    file_content = io.BytesIO(b"AssetID;Hostname\n1;test\n")
    file_content.name = "test.csv"
    data = {'step': '1', 'file': file_content}
    response = logged_in_client.post(url, data)
    assert response.status_code == 200
    assert response.context['step'] == 1
    assert 'select_form' in response.context
    assert logged_in_client.session['devices'] == [{'foo': 'bar'}]


@pytest.mark.django_db
@patch("nac.forms.FileUploadForm")
def test_post_step1_invalid(mock_form, logged_in_client):
    url = reverse('file_import')
    mock_form_instance = MagicMock()
    mock_form_instance.is_valid.return_value = False
    mock_form.return_value = mock_form_instance
    file_content = io.BytesIO(b"AssetID;Hostname\n1;test\n")
    file_content.name = "test.csv"
    data = {'step': '1', 'file': file_content}
    response = logged_in_client.post(url, data)
    assert response.status_code == 200
    assert response.context['step'] == 1
    assert 'form' in response.context


@pytest.mark.django_db
@patch("helper.file_integration._modify_macs")
@patch("helper.file_integration.handle_devices")
@patch("nac.forms.FileUploadSelectForm")
def test_post_step2_valid(mock_select_form, mock_handle_devices, mock_modify_macs, logged_in_client):
    url = reverse('file_import')
    session = logged_in_client.session
    session['devices'] = [{'foo': 'bar'}]
    session.save()
    mock_select_form_instance = MagicMock()
    mock_select_form_instance.is_valid.return_value = True
    mock_select_form_instance.cleaned_data = {
        "administration_group": MagicMock(),
        "dns_domain": MagicMock(),
    }
    mock_select_form.return_value = mock_select_form_instance
    mock_handle_devices.return_value = ([{'device': 1}], [])
    mock_modify_macs.return_value = [{'device': 1}]
    data = {'step': '2'}
    response = logged_in_client.post(url, data)
    assert response.status_code == 200
    assert 'devices' in response.context
    assert 'invalid_devices' in response.context


@pytest.mark.django_db
@patch("nac.forms.FileUploadSelectForm")
def test_post_step2_invalid(mock_select_form, logged_in_client):
    url = reverse('file_import')
    session = logged_in_client.session
    session['devices'] = [{'foo': 'bar'}]
    session.save()
    mock_select_form_instance = MagicMock()
    mock_select_form_instance.is_valid.return_value = False
    mock_select_form.return_value = mock_select_form_instance
    data = {'step': '2'}
    response = logged_in_client.post(url, data)
    assert response.status_code == 200
    assert 'select_form' in response.context


@pytest.mark.django_db
@patch("helper.file_integration.save_checked_objects_in_db")
def test_post_step3(mock_save_checked, logged_in_client):
    url = reverse('file_import')
    session = logged_in_client.session
    session['devices'] = [{'id': 1}]
    session.save()
    mock_save_checked.return_value = ['device1']
    data = {'step': '3', 'markedForImport': ['1']}
    response = logged_in_client.post(url, data)
    assert response.status_code == 200
    assert response.context['step'] == 3


@pytest.mark.django_db
@patch("helper.file_integration.get_devices", side_effect=Exception("Fehler!"))
@patch("nac.forms.FileUploadForm")
def test_post_step1_exception(mock_form, mock_get_devices, logged_in_client):
    url = reverse('file_import')
    mock_form_instance = MagicMock()
    mock_form_instance.is_valid.return_value = True
    mock_form.return_value = mock_form_instance
    file_content = io.BytesIO(b"AssetID;Hostname\n1;test\n")
    file_content.name = "test.csv"
    data = {'step': '1', 'file': file_content}
    response = logged_in_client.post(url, data)
    assert response.status_code == 200
