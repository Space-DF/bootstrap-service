FROM python:3.10-alpine AS builder

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/bootstrap-service

RUN apk add --no-cache \
    build-base \
    libffi-dev \
    git

WORKDIR /install

# install private repo
RUN --mount=type=secret,id=github_token \
    pip install --no-cache-dir --prefix=/install \
    git+https://$(cat /run/secrets/github_token)@github.com/Space-DF/django-common-utils.git@dev

# install python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.10-alpine

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/bootstrap-service
ENV DJANGO_SETTINGS_MODULE=bootstrap_service.settings

RUN apk add --no-cache \
    curl \
    bash \
    netcat-openbsd \
    libffi

WORKDIR /app

# copy only installed python packages
COPY --from=builder /install /usr/local

# copy source code
COPY . .

RUN ["chmod", "+x", "./docker-entrypoint.sh"]

# Run the production server
ENTRYPOINT ["./docker-entrypoint.sh"]