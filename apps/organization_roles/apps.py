from django.apps import AppConfig


class OrganizationRoleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.organization_roles"

    def ready(self):
        from . import signals  # noqa: F401
