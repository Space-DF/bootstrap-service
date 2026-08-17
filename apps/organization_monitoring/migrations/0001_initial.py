import uuid

from django.db import migrations, models

from apps.organization_monitoring.constants import MonitoringType


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("organization", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrganizationMonitoring",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("cell_size", models.FloatField(default=50.0)),
                (
                    "type",
                    models.CharField(default=MonitoringType.WATER_LEVEL, max_length=50),
                ),
                ("thresholds", models.JSONField(blank=True, default=dict)),
                ("colors", models.JSONField(blank=True, default=dict)),
                ("display_settings", models.JSONField(blank=True, default=dict)),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="monitoring_settings",
                        to="organization.Organization",
                    ),
                ),
            ],
            options={"db_table": "organization_monitoring"},
        ),
        migrations.AddConstraint(
            model_name="organizationmonitoring",
            constraint=models.UniqueConstraint(
                fields=["organization", "type"], name="unique_monitoring_type_per_org"
            ),
        ),
    ]
