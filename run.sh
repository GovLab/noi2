#!/bin/bash -e

if [ "$NOI_ENVIRONMENT" == production ]; then
    cd /noi && gunicorn wsgi:application -b 0.0.0.0:5000
elif [ "$NOI_ENVIRONMENT" == celery ]; then
    #cd /noi && celery worker -Q celery -A celery_core.celery --loglevel=debug
    #cd /noi && celery -A celery_core.celery beat --loglevel=debug
    cd /noi && celery -A celery_core.celery worker -B --loglevel=debug
else
    NOI_ENVIRONMENT=development python /noi/manage.py runserver --host 0.0.0.0
fi
