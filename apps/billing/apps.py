from django.apps import AppConfig


class BillingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.billing"

    def ready(self):
        # Importing tasks connects the task_failure signal handler defined there.
        from apps.billing import tasks  # noqa: F401
