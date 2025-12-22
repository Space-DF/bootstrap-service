FROM python:3.10-alpine

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/bootstrap-service
ENV DJANGO_SETTINGS_MODULE=bootstrap_service.settings

RUN apk add --no-cache \
    build-base \
    libffi-dev \
    curl \
    bash \
    netcat-openbsd

COPY ./django-common-utils /django-common-utils
RUN pip install /django-common-utils

COPY ./bootstrap-service /bootstrap-service
WORKDIR /bootstrap-service

RUN pip install -r requirements.txt

RUN ["chmod", "+x", "./docker-entrypoint.sh"]

# Run the production server
ENTRYPOINT ["./docker-entrypoint.sh"]