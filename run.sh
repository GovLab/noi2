#!/bin/bash -e

python /noi/manage.py drop_and_create_db -v
python /noi/manage.py populate_db
python /noi/manage.py runserver --host 0.0.0.0
