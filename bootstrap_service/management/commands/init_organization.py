import os
import time
import uuid
from datetime import datetime

from common.rabitmq.rabbitmq_provisioner import RabbitMQProvisioner
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.module_loading import import_string
from kombu import Exchange

from utils.check_tenant_exists import check_tenant_exists
from utils.event_publisher import publish_org_event


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--org-name", type=str, help="Name of the organization", required=False
        )
        parser.add_argument(
            "--org-slug", type=str, help="Slug name of the organization", required=False
        )
        parser.add_argument(
            "--owner-email", type=str, help="Owner email", required=False
        )
        parser.add_argument(
            "--owner-password", type=str, help="Owner password", required=False
        )

    def handle(self, *args, **kwargs):  # noqa: C901
        org_name = kwargs.get("org_name") or os.getenv("ORG_NAME")
        org_slug = kwargs.get("org_slug") or os.getenv("ORG_SLUG")
        owner_email = kwargs.get("owner_email") or os.getenv("OWNER_EMAIL")
        owner_password = kwargs.get("owner_password") or os.getenv("OWNER_PASSWORD")
        org_id = str(uuid.uuid4())

        self.stdout.write(
            self.style.SUCCESS(
                f"Creating schema for organization: {org_name} ({org_slug})"
            )
        )

        # Check if tenant already exists
        provisioner = RabbitMQProvisioner()
        existing = check_tenant_exists(provisioner, org_slug)
        if existing:
            self.stdout.write(
                self.style.WARNING(
                    f"Organization '{org_slug}' already provisioned in vhost '{existing['vhost']}'. "
                )
            )
            result = existing
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Provisioning organization '{org_slug}'...")
            )
            result = provisioner.provision_tenant(org_id, org_slug, 1112)

        # Publish org.created event with minimal required data
        publish_org_event(
            "org.created",
            str(uuid.uuid4()),
            timezone.now().isoformat(),
            {
                "id": org_id,
                "slug": org_slug,
                "name": org_name,
                "vhost": result.get("vhost", ""),
                "amqp_url": result.get("amqp_url", ""),
                "exchange": result.get("exchange", f"{org_slug}.exchange"),
                "transformer_queue": result.get(
                    "transformer_queue", f"{org_slug}.transformer.queue"
                ),
                "transformed_queue": result.get(
                    "transformed_queue", f"{org_slug}.transformed.data.queue"
                ),
                "is_active": True,
                "created_at": timezone.now().isoformat(),
                "updated_at": timezone.now().isoformat(),
            },
        )

        celery_app = import_string(settings.CELERY_APP)
        encrypted_password = make_password(owner_password)

        celery_app.send_task(
            name="spacedf.tasks.new_organization",
            exchange=Exchange("new_organization", type="fanout"),
            routing_key="new_organization",
            kwargs={
                "id": org_id,
                "name": org_name,
                "slug_name": org_slug,
                "is_active": True,
                "owner": {
                    "id": str(uuid.uuid4()),
                    "email": owner_email,
                    "password": encrypted_password,
                },
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Dispatched schema creation task for organization '{org_name}' with ID: {org_id}"
            )
        )

        self.stdout.write("Waiting for task processing...")
        time.sleep(5)
        self.stdout.write(self.style.SUCCESS("Task dispatch complete."))
