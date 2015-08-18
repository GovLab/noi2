#!/bin/bash

./manage.sh db upgrade
NOI_ENVIRONMENT=production docker-compose up > out.log 2> err.log &
