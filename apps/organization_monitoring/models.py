from common.models.base_model import BaseModel
from django.db import models

from apps.organization.models import Organization
from apps.organization_monitoring.constants import MonitoringType


class OrganizationMonitoring(BaseModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="monitoring_settings",
    )
    cell_size = models.FloatField(default=50.0)
    type = models.CharField(
        max_length=50,
        default=MonitoringType.WATER_LEVEL,
        choices=MonitoringType.choices,
    )
    thresholds = models.JSONField(default=dict, blank=True)
    colors = models.JSONField(default=dict, blank=True)
    display_settings = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "organization_monitoring"
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "type"],
                name="unique_monitoring_type_per_org",
            )
        ]
