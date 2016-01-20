#!/bin/bash

python /noi/manage.py wait_for_db

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
    python /noi/develop.py
fi
