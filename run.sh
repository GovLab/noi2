#!/bin/bash

function pg_wait {
  while : ; do
    pg_isready --host db --user postgres
    if [ $? == 0 ]; then
      break
    else
      sleep 0.1
    fi
  done
}

pg_wait

set -e
if [ "$NOI_ENVIRONMENT" == production ]; then
    cd /noi
    python manage.py db upgrade
    python manage.py translate_compile
    gunicorn wsgi:application -b 0.0.0.0:5000
elif [ "$NOI_ENVIRONMENT" == celery ]; then
    #cd /noi && celery worker -Q celery -A celery_core.celery --loglevel=debug
    #cd /noi && celery -A celery_core.celery beat --loglevel=debug
    cd /noi && celery -A celery_core.celery worker -B --loglevel=debug
else
    python /noi/manage.py db upgrade
    python /noi/manage.py translate_compile
    NOI_ENVIRONMENT=development python /noi/manage.py runserver --host 0.0.0.0
fi
