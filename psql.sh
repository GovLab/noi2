#!/bin/bash -e

docker-compose run web psql --host db postgres postgres
