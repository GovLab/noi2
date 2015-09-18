#!/bin/bash -e

docker-compose run app nosetests -w /noi $@
