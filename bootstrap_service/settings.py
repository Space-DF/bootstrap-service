# Copyright 2026 Digital Fortress.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Django settings for bootstrap_service project.
"""

import os
from datetime import timedelta
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
COMMON_UTILS_DIR = Path(__file__).resolve().parent.parent.parent / "django-common-utils"

SECRET_KEY = os.getenv(
    "SECRET_KEY", "django-insecure-*$0b8ibx7uzk45cm+fxw7*jj(yzi2ye!l4+!dnyxa-u-nbuz=q"
)

DJANGO_SETTINGS_MODULE = "bootstrap_service.settings"
ROOT_URLCONF = "bootstrap_service.urls"

DEBUG = True
ALLOWED_HOSTS = ["*"]

HOST = os.getenv("HOST", "http://localhost:8000/")
HOST_FRONTEND_ADMIN = os.getenv("HOST_FRONTEND_ADMIN", "http://localhost:3000/")  # noqa

# Timezone configuration
USE_TZ = True
TIME_ZONE = "UTC"

# Minimal installed apps for management commands
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_yasg",
    "common.apps.refresh_tokens",
    "bootstrap_service",
    "apps.organization",
    "apps.organization_roles",
    "apps.authentication",
]

REFRESH_TOKEN_CLASS = "rest_framework_simplejwt.tokens.RefreshToken"  # nosec B105

AWS_S3 = {
    "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID", ""),  # noqa
    "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY", ""),  # noqa
    "AWS_STORAGE_BUCKET_NAME": os.getenv("AWS_STORAGE_BUCKET_NAME", ""),  # noqa
    "AWS_REGION": os.getenv("AWS_REGION", "us-east-1"),  # noqa
}


AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]
# JWT config
JWT_PRIVATE_KEY = os.getenv("JWT_PRIVATE_KEY")
JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY")

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "RS256",
    "SIGNING_KEY": JWT_PRIVATE_KEY,
    "VERIFYING_KEY": JWT_PUBLIC_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(days=7),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=10),
    "TOKEN_REFRESH_SERIALIZER": "common.apps.refresh_tokens.serializers.CustomTokenRefreshSerializer",
    "TOKEN_OBTAIN_SERIALIZER": "apps.authentication.serializers.TokenObtainPairSerializer",
}
REFRESH_TOKEN_CLASS = "rest_framework_simplejwt.tokens.RefreshToken"  # nosec B105

# auth config
AUTH_USER_MODEL = "authentication.RootUser"
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = "email"

# Middleware configuration (required for admin application)
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = "static/"
STATICFILES_DIRS = (os.path.join(COMMON_UTILS_DIR, "common", "static"),)

# Templates configuration (required for admin application)
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [COMMON_UTILS_DIR / "common" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://default:password@rabbitmq:5672/")
RABBITMQ_MANAGEMENT_API_URL = os.getenv(
    "RABBITMQ_MANAGEMENT_API_URL", "http://rabbitmq:15672"
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
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "amqp://default:password@rabbitmq")
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

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.getenv("DB_NAME", "spacedf_console_service"),
        "USER": os.getenv("DB_USERNAME", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", "postgres"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", 25060),
    }
}

DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
