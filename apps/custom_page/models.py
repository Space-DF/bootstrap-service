from common.models.base_model import BaseModel
from django.db import models

from apps.custom_page.constants import PageTypes
from apps.organization_setting.models import OrganizationSetting


class CustomPage(BaseModel):
    organization_setting = models.ForeignKey(
        OrganizationSetting,
        on_delete=models.CASCADE,
        related_name="organization_setting_custom_page",
        null=True,
        blank=True,
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
