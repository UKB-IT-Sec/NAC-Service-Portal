# NAC-Service-Portal
[![Django CI](https://github.com/UKB-IT-Sec/NAC-Service-Portal/actions/workflows/django.yml/badge.svg)](https://github.com/UKB-IT-Sec/NAC-Service-Portal/actions/workflows/django.yml)

## Install

### Pre-Requirements
Apache2 and mod_wsgi must be installed and enabled.

### Install
```
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
python3 manage.py makemigrations
python3 manage.py migrate
```

## Run Test-Server
```
cd src/
source venv/bin/activate
python manage.py runserver
```
Test Server should be available at `localhost:8000`

## Account creation

For admin access (creating accounts and groups) you need to create a superuser account.

```
python manage.py createsuperuser
```
Log in to the admin panel at http://127.0.0.1:8000/admin/ with your superuser credentials. Here you can create user accounts. 


