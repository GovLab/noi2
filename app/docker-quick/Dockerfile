#
# Network of Innovators Dockerfile for web
#
# https://github.com/govlab/noi2
#

FROM thegovlab/noi2:latest
MAINTAINER Atul Varma <atul@thegovlab.org>

RUN apt-get install -y git

COPY requirements.quick.txt /noi/app/
RUN pip install --upgrade -r /noi/app/requirements.quick.txt
