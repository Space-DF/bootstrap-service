from rest_framework import serializers

from apps.organization_monitoring.models import OrganizationMonitoring


class OrganizationMonitoringSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationMonitoring
        fields = [
            "id",
            "cell_size",
            "type",
            "thresholds",
            "colors",
            "display_settings",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
            "created_at": {"read_only": True},
            "updated_at": {"read_only": True},
        }
