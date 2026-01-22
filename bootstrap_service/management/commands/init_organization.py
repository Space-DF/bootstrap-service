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

import os
import uuid
from datetime import datetime

from common.celery.task_senders import send_task
from common.rabitmq.rabbitmq_provisioner import RabbitMQProvisioner
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.forms.models import model_to_dict
from django.utils import timezone

from apps.authentication.models import RootUser
from apps.organization.models import Organization
from apps.organization_roles.constants import OrganizationRoleType
from apps.organization_roles.models import OrganizationRoleUser
from apps.organization_roles.services import (
    create_default_organization_role_by_policy_tag,
    create_default_policies,
)
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

    def _get_config(self, **kwargs):
        """Extract configuration from arguments or environment variables."""
        return {
            "org_name": kwargs.get("org_name") or os.getenv("ORG_NAME"),
            "org_slug": kwargs.get("org_slug") or os.getenv("ORG_SLUG"),
            "owner_email": kwargs.get("owner_email") or os.getenv("OWNER_EMAIL"),
            "owner_password": kwargs.get("owner_password")
            or os.getenv("OWNER_PASSWORD"),
        }

    def _provision_rabbitmq(self, provisioner, org_id, org_slug):
        """Provision or retrieve existing RabbitMQ resources."""
        existing = check_tenant_exists(provisioner, org_slug)
        if existing:
            self.stdout.write(
                self.style.WARNING(
                    f"Organization '{org_slug}' already provisioned in vhost '{existing['vhost']}'"
                )
            )
            return existing

        self.stdout.write(
            self.style.SUCCESS(f"Provisioning organization '{org_slug}'...")
        )
        return provisioner.provision_tenant(org_id, org_slug, 1112)

    def _publish_org_event(self, org_id, org_slug, org_name, result):
        """Publish organization created event."""
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

    def _create_organization_with_roles(self, org_id, org_name, org_slug, result):
        """Create organization with default policies and roles."""
        organization = Organization.objects.create(
            id=org_id,
            name=org_name,
            slug_name=org_slug,
            logo="",
            is_active=True,
            rabbitmq_vhost=result.get("vhost", ""),
            rabbitmq_provisioned_at=timezone.now(),
        )
        self.stdout.write(self.style.SUCCESS(f"Created organization: {org_name}"))

        create_default_policies(organization)
        self.stdout.write(self.style.SUCCESS("Created default policies"))

        role_mappings = [
            (OrganizationRoleType.OWNER_ROLE, "administrator"),
            (OrganizationRoleType.ADMIN_ROLE, "full-access"),
            (OrganizationRoleType.VIEWER_ROLE, "read-only"),
            (OrganizationRoleType.EDITOR_ROLE, "edit-only"),
        ]

        owner_role = None
        for role_type, policy_tag in role_mappings:
            role = create_default_organization_role_by_policy_tag(
                role_type, policy_tag, organization
            )
            if role_type == OrganizationRoleType.OWNER_ROLE:
                owner_role = role

        self.stdout.write(self.style.SUCCESS("Created default roles"))
        return organization, owner_role

    def _send_celery_task(self, org_id, org_name, org_slug, user):
        """Send initialization task to Celery."""
        send_task(
            name="new_organization",
            message={
                "id": org_id,
                "name": org_name,
                "slug_name": org_slug,
                "is_active": True,
                "owner": model_to_dict(
                    user,
                    fields=[
                        "id",
                        "email",
                        "password",
                    ],
                ),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
        )

    def _send_delete_celery_task(self, org_slug):
        """Send organization deletion task to Celery."""
        send_task(
            name="delete_organization",
            message={
                "slug_name": org_slug,
            },
        )

    def _delete_organization(self, provisioner, organization):
        """Delete organization and cascade-related data from all services."""
        org_slug = organization.slug_name
        org_id = organization.id
        vhost_name = organization.rabbitmq_vhost

        publish_org_event(
            "org.deleted",
            str(uuid.uuid4()),
            timezone.now().isoformat(),
            {
                "id": str(org_id),
                "slug": org_slug,
                "deleted_at": timezone.now().isoformat(),
            },
        )

        # Send Celery task for deletion
        self._send_delete_celery_task(org_slug)

        # Delete RabbitMQ resources
        provisioner.delete_tenant(vhost_name, org_slug)
        organization.delete()

        self.stdout.write(
            self.style.SUCCESS(f"Deleted organization '{org_slug}' (ID: {org_id})")
        )

    def handle(self, *args, **kwargs):
        config = self._get_config(**kwargs)
        org_name, org_slug = config["org_name"], config["org_slug"]
        owner_email, owner_password = config["owner_email"], config["owner_password"]
        encrypted_password = make_password(owner_password)
        org_id = str(uuid.uuid4())
        provisioner = RabbitMQProvisioner()

        existing_org = Organization.objects.first()
        if existing_org and existing_org.slug_name != org_slug:
            self.stdout.write(
                self.style.WARNING(
                    f"Organization slug changed from '{existing_org.slug_name}' to '{org_slug}'. "
                    "Deleting old organization..."
                )
            )
            self._delete_organization(provisioner, existing_org)
            existing_org = None

        if not existing_org:
            result = self._provision_rabbitmq(provisioner, org_id, org_slug)
            self.stdout.write(
                self.style.SUCCESS(f"Creating organization: {org_name} ({org_slug})")
            )
            # Create organization, roles, and assign owner
            user, _ = RootUser.objects.get_or_create(
                email=owner_email, defaults={"password": encrypted_password}
            )
            self.stdout.write(self.style.SUCCESS(f"Created owner user: {owner_email}"))
            _, owner_role = self._create_organization_with_roles(
                org_id, org_name, org_slug, result
            )
            OrganizationRoleUser(root_user=user, organization_role=owner_role).save()
            self.stdout.write(
                self.style.SUCCESS(f"Assigned owner role to {owner_email}")
            )

            # Publish organization event
            self._publish_org_event(org_id, org_slug, org_name, result)
            self._send_celery_task(org_id, org_name, org_slug, user)
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"Organization '{org_slug}' already exists. Skipping org creation..."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Organization '{org_name}' initialized with ID: {org_id}"
            )
        )
