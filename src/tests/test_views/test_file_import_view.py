import pytest
import io
from django.urls import reverse
from unittest.mock import patch, MagicMock
from helper.file_integration import ESSENTIAL_HEADER
from nac.forms import FileUploadSelectForm


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
@patch.object(FileUploadSelectForm, "is_valid", return_value=False)
def test_post_step2_invalid(mock_is_valid, logged_in_client):
    url = reverse('file_import')
    session = logged_in_client.session
    session['devices'] = [{'foo': 'bar'}]
    session.save()
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
