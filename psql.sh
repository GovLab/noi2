#!/bin/bash -e

docker-compose run app psql --host db postgres postgres
