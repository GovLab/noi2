#!/bin/bash -e

docker-compose run --service-ports app nosetests -w /noi $@
