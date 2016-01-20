#
# Network of Innovators Dockerfile for web
#
# https://github.com/govlab/noi2
#

FROM python:2.7
MAINTAINER Atul Varma <atul@thegovlab.org>

RUN curl -sL https://deb.nodesource.com/setup_0.12 | bash - && \
  apt-get install -y nodejs && \
  npm install -g postcss-cli autoprefixer

COPY requirements.txt /

RUN pip install -r /requirements.txt

EXPOSE 5000
