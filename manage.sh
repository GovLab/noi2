#!/bin/bash -e

docker-compose run app python manage.py $@
