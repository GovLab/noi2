#!/bin/bash

docker-compose -f docker-compose.yml -f production.yml stop
docker-compose -f docker-compose.yml -f production.yml up -d
