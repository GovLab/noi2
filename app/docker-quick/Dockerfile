#
# Network of Innovators Dockerfile for web
#
# https://github.com/govlab/noi2
#

FROM thegovlab/noi2:docker-base-0.2
MAINTAINER Atul Varma <atul@thegovlab.org>

COPY requirements.quick.txt /noi/app/
RUN pip install --upgrade -r /noi/app/requirements.quick.txt

# http://stackoverflow.com/a/16745106/2422398
RUN /usr/bin/yes | pip uninstall nose
