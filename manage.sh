#!/bin/bash -e

docker-compose run app python /noi/manage.py $@
