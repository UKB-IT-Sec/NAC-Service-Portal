# NAC-Service-Portal
[![Django CI](https://github.com/UKB-IT-Sec/NAC-Service-Portal/actions/workflows/django.yml/badge.svg)](https://github.com/UKB-IT-Sec/NAC-Service-Portal/actions/workflows/django.yml)

## Install
```
cd src/
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

## Export Assets to LDAP Server
You have to add `resources/appl-NAC.schema` to your ldap server before an import is possible.

Default config file for ldap export can be found at `config/export.cnf`
```
pyhton3 -m manage.py export_to_ldap
```

## Public Funding
![Funded by European Union](https://ec.europa.eu/regional_policy/images/information-sources/logo-download-center/nextgeneu_en.jpg)