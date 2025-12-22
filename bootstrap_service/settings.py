"""
Django settings for bootstrap_service project.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv(
    "SECRET_KEY", "django-insecure-*$0b8ibx7uzk45cm+fxw7*jj(yzi2ye!l4+!dnyxa-u-nbuz=q"
)

DJANGO_SETTINGS_MODULE = "bootstrap_service.settings"

DEBUG = False
ALLOWED_HOSTS = ["*"]

# Timezone configuration
USE_TZ = True
TIME_ZONE = "UTC"

# Minimal installed apps for management commands
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "bootstrap_service",
]

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
RABBITMQ_MANAGEMENT_API_URL = os.getenv(
    "RABBITMQ_MANAGEMENT_API_URL", "http://localhost:15672"
)
RABBITMQ_DEFAULT_USER = os.getenv("RABBITMQ_DEFAULT_USER", "default")
RABBITMQ_DEFAULT_PASSWORD = os.getenv("RABBITMQ_DEFAULT_PASS", "password")

# Organization Events Exchange (for notifying transformer, broker-bridge services)
ORG_EVENTS_EXCHANGE = "org.events"
ORG_TRANSFORMER_QUEUE = "transformer.org.events.queue"
ORG_BROKER_BRIDGE_QUEUE = "broker-bridge.org.events.queue"
ORG_EVENTS_ROUTING_KEY = "org.*"
ORG_CONSOLE_QUEUE = "console.org.discovery.queue"
ORG_DISCOVERY_ROUTING_KEY = "org.discovery.request"

# Celery Configuration (for sending tasks only)
CELERY_APP = "bootstrap_service.celery.app"
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@localhost")
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# EMQX Configuration
EMQX_API_URL = os.getenv("EMQX_API_URL", "http://emqx:18083/api/v5")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_MQTT_PORT = int(os.getenv("RABBITMQ_MQTT_PORT", "1883"))
EMQX_RULE_ID = os.getenv("EMQX_RULE_ID", "rabbitmq_device_messages")
EMQX_RULE_SQL = os.getenv("EMQX_RULE_SQL", 'SELECT * FROM "tenant/+/device/data"')
EMQX_USERNAME = os.getenv("EMQX_USERNAME", "user1")
EMQX_PASSWORD = os.getenv("EMQX_PASSWORD", "password123")

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
