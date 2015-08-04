#
# Network of Innovators Dockerfile for web
#
# https://github.com/govlab/noi2
#

FROM debian:jessie
MAINTAINER John Krauss <john@thegovlab.org>

RUN apt-get update && apt-get -y dist-upgrade
RUN apt-get install -yqq python-pip libpq-dev python-dev postgresql-client-9.4

RUN mkdir -p /noi/app
COPY . /noi/app

RUN pip install -r /noi/app/requirements.txt
