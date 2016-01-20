#!/bin/bash -e

docker-compose run --service-ports app nosetests --with-doctest -I manage.py -I wsgi.py $@
