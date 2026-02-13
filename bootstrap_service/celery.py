import importlib.util
import os
import sys

if importlib.util.find_spec("common") is None:
    sys.path.append(os.path.abspath(os.path.join("..", "django-common-utils")))

from celery import Celery
from common.celery import constants
from dotenv import load_dotenv
from kombu import Exchange, Queue

load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bootstrap_service.settings")
app = Celery("bootstrap_service")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

TASKS_CONSOLE = [
    constants.CONSOLE_SERVICE_ADD_OR_REMOVE_SPACE,
]

existing = {queue.name: queue for queue in (app.conf.task_queues or ())}
routes = dict(app.conf.task_routes or {})

for name in TASKS_CONSOLE:
    if name not in existing:
        existing[name] = Queue(
            name,
            exchange=Exchange(name, type="direct"),
            routing_key=f"spacedf.tasks.{name}",
            durable=True,
        )
    routes[f"spacedf.tasks.{name}"] = {
        "queue": name,
        "routing_key": f"spacedf.tasks.{name}",
    }

app.conf.task_queues = tuple(existing.values())
app.conf.task_routes = routes
