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
    python manage.py build_sass
    gunicorn wsgi:application -b 0.0.0.0:5000
else
    python /noi/manage.py db upgrade
    python /noi/manage.py translate_compile
    NOI_ENVIRONMENT=development python /noi/develop.py
fi
