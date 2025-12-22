import importlib.util
import os
import sys

if importlib.util.find_spec("common") is None:
    sys.path.append(os.path.abspath(os.path.join("..", "django-common-utils")))

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bootstrap_service.settings")
app = Celery("bootstrap_service")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
