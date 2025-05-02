import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_home(client):
    url = reverse('home')
    response = client.get(url)
    assert b'You are not logged in.' in response.content
    assert response.status_code == 200


@pytest.mark.django_db
def test_user_login_page(client):
    response = client.get('/accounts/login/')
    assert b'login' in response.content
    assert response.status_code == 200


def test_home_template(client):
    url = reverse("home")
    response = client.get(url)
    templates = [t.name for t in response.templates]
    assert "home.html" in templates
    assert b"<h1>NAC Self-Service-Portal</h1>" in response.content
