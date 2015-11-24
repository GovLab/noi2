#!/bin/bash -e

docker-compose run --service-ports app nosetests -w /noi --with-doctest -I manage.py -I wsgi.py -I celery_core.py $@
