from common.models.base_model import BaseModel
from django.db import models

from apps.custom_email.constants import EmailTypes
from apps.organization_setting.models import OrganizationSetting


class OrganizationEmail(BaseModel):
    organization_setting = models.ForeignKey(
        OrganizationSetting,
        on_delete=models.CASCADE,
        related_name="organization_setting_custom_emails",
        null=True,
        blank=True,
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
                fields=["organization_setting", "email_type"],
                name="unique_organization_email_type",
            )
        ]
