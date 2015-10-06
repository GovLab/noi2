#!/bin/bash -e

docker-compose run -e PGPASSWORD=$POSTGRES_PASSWORD app psql --host db noi noi
