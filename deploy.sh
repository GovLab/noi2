#!/bin/bash

NOI_ENVIRONMENT=production docker-compose stop
NOI_ENVIRONMENT=production docker-compose up -d
