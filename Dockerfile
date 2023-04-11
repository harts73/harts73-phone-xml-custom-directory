FROM python:latest
ENV PYTHONUNBUFFERED 1

RUN apt-get update
RUN apt-get install -y nano
RUN pip install pip -U
RUN pip install flask gunicorn uwsgi ldap3

ENV LDAP_USER="TEST\svc_ldap"
ENV PASSWORD=supersecret
ENV LDAP_SERVER=10.1.1.1
ENV LDAP_PORT=389
ENV LDAP_SEARCH_BASE="OU=employees,dc=test,dc=local"
# URL is the IP or name that is running this docker container. The phones will use it to connect.
ENV URL="http://10.1.1.2:8119"

RUN mkdir /app
ADD ./app /app
WORKDIR /app

ENTRYPOINT ["/bin/bash","-c","gunicorn -w 4 --bind 0.0.0.0:8119 --log-level=debug wsgi:app"]