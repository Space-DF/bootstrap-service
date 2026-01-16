#!/bin/ash
set -e

echo "Organization Service Starting..."
echo "ORG_NAME: ${ORG_NAME:-not set}"
echo "ORG_SLUG: ${ORG_SLUG:-not set}"
echo "OWNER_EMAIL: ${OWNER_EMAIL:-not set}"

echo "Waiting for RabbitMQ AMQP on rabbitmq:5672..."
until nc -z rabbitmq 5672; do
  echo "RabbitMQ not ready, retrying in 2 seconds..."
  sleep 2
done
echo "RabbitMQ is ready"

echo "Waiting for EMQX on emqx:18083..."
until nc -z emqx 18083; do
  echo "EMQX not ready, retrying in 2 seconds..."
  sleep 2
done
echo "EMQX is ready"

echo "Running database migrations..."
python manage.py migrate

echo "Running organization initialization..."
python manage.py init_organization \
  --org-name="${ORG_NAME}" \
  --org-slug="${ORG_SLUG}" \
  --owner-email="${OWNER_EMAIL}" \
  --owner-password="${OWNER_PASSWORD}"

echo "Organization initialization complete"

# Start Gunicorn and Celery
gunicorn --worker-class gevent --bind 0.0.0.0:80 --access-logfile - bootstrap_service.wsgi \ 
& celery -A bootstrap_service worker -l info -c 1
