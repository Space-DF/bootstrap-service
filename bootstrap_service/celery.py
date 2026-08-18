import importlib.util
import os
import sys

if importlib.util.find_spec("common") is None:
    sys.path.append(os.path.abspath(os.path.join("..", "django-common-utils")))

from celery import Celery
from common.celery import constants
from common.celery.routing import (
    append_unique_task_queues,
    setup_subscription_task_routing,
)
from console_service.constants import CONSOLE_DOWNGRADE_TASK, CONSOLE_UPGRADE_TASK
from dotenv import load_dotenv
from kombu import Exchange, Queue

load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bootstrap_service.settings")
app = Celery("bootstrap_service")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
setup_subscription_task_routing(
    [
        {
            "task_name": CONSOLE_DOWNGRADE_TASK,
            "service": "console",
            "lifecycle": "downgrade",
        },
        {
            "task_name": CONSOLE_UPGRADE_TASK,
            "service": "console",
            "lifecycle": "upgrade",
        },
    ]
)


TASKS_CONSOLE = [
    constants.CONSOLE_SERVICE_ADD_OR_REMOVE_SPACE,
    constants.CONSOLE_SERVICE_DELETE_UPLOAD_FILE,
]

routes = dict(app.conf.task_routes or {})
queues = []

for name in TASKS_CONSOLE:
    queues.append(
        Queue(
            name,
            exchange=Exchange(name, type="direct"),
            routing_key=f"spacedf.tasks.{name}",
            durable=True,
        )
    )
    routes[f"spacedf.tasks.{name}"] = {
        "queue": name,
        "routing_key": f"spacedf.tasks.{name}",
    }

append_unique_task_queues(app, queues)
app.conf.task_routes = routes
