# NAC-Service-Portal

## Install

### Pre-Requirements
Apache2 and mod_wsgi must be installed and enabled.

### Install
```
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

## Run Test-Server
```
cd src/
source venv/bin/activate
python manage.py runserver
```
Test Server should be available at `localhost:8000`