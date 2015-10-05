#
# Network of Innovators Dockerfile for web
#
# https://github.com/govlab/noi2
#

FROM debian:jessie
MAINTAINER John Krauss <john@thegovlab.org>

RUN apt-get update && apt-get -y dist-upgrade
RUN apt-get install -y python-pip libpq-dev python-dev postgresql-client-9.4 libffi-dev curl

RUN mkdir -p /noi/app
COPY . /noi/app

RUN curl https://bootstrap.pypa.io/ez_setup.py -o - | python # update setuptools
RUN pip install -r /noi/app/requirements.txt

EXPOSE 5000
