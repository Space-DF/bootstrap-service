from django.apps import AppConfig

_events_initialized = False


class OrganizationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.organization"

    def ready(self):
        global _events_initialized
        if _events_initialized:
            return

        from utils.event_publisher import EventPublisher

        publisher = EventPublisher()
        connection, _ = publisher.setup_org_event()
        if connection:
            connection.close()

        publisher.start_discovery_listener()
        _events_initialized = True
