#!/bin/bash -e

if [ "$NOI_ENVIRONMENT" == production ]; then
    cd /noi && gunicorn wsgi:application -b 0.0.0.0:5000
else
    NOI_ENVIRONMENT=development python /noi/manage.py runserver --host 0.0.0.0
fi
