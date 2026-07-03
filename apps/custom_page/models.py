from common.models.base_model import BaseModel
from django.db import models

from apps.custom_page.constants import PageTypes
from apps.organization.models import Organization


class CustomPage(BaseModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="organization_custom_page",
    )
    page_type = models.CharField(max_length=255, choices=PageTypes.choices)
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    theme_colors = models.JSONField(default=dict, blank=True)
    background_image = models.CharField(max_length=500, blank=True, default="")
    show_logo = models.BooleanField(default=True)

    class Meta:
        db_table = "custom_pages"
        ordering = ["-created_at"]
