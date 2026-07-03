from common.models.base_model import BaseModel
from django.db import models

from apps.custom_email.constants import EmailTypes
from apps.organization.models import Organization


class OrganizationEmail(BaseModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="organization_custom_emails",
    )
    email_type = models.CharField(max_length=255, choices=EmailTypes.choices)
    sender_name = models.CharField(max_length=255, blank=True)
    sender_email = models.CharField(max_length=255, blank=True)
    theme_colors = models.JSONField(default=dict, blank=True)
    footer_text = models.TextField(blank=True)
    header_image = models.CharField(max_length=500, blank=True, default="")
    show_logo = models.BooleanField(default=True)
    social_links = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "custom_emails"
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "email_type"],
                name="unique_organization_email_type",
            )
        ]
