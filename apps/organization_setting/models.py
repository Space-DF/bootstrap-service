from common.models.base_model import BaseModel
from django.db import models

from apps.organization.models import Organization


class OrganizationSetting(BaseModel):
    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name="organization_settings",
    )
    brand_name = models.CharField(max_length=255, blank=True)
    site_title = models.CharField(max_length=255, blank=True)
    site_description = models.TextField(blank=True)
    border_radius = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "organization_settings"


class OrganizationTheme(BaseModel):
    setting = models.ForeignKey(
        OrganizationSetting,
        on_delete=models.CASCADE,
        related_name="themes",
    )
    theme_key = models.CharField(max_length=50)
    favicon = models.CharField(max_length=500, blank=True)
    logo = models.CharField(max_length=500, blank=True)
    theme_colors = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "organization_themes"
        constraints = [
            models.UniqueConstraint(
                fields=["setting", "theme_key"],
                name="unique_organization_theme_key_per_setting",
            )
        ]
