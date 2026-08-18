from apps.organization.models import Organization
from apps.organization_monitoring.constants import MonitoringType
from apps.organization_monitoring.models import OrganizationMonitoring

DEFAULT_MONITORING_VALUES = {
    "cell_size": 50.0,
    "thresholds": {"safe": 0.1, "caution": 0.3, "warning": 0.6},
    "colors": {
        "safe": "#08B94E",
        "caution": "#EBA622",
        "warning": "#FD6665",
        "danger": "#E5372B",
    },
    "display_settings": {"device_icons": True, "water_column": True, "coverage": True},
}


def create_default_organization_monitoring(organization: Organization):
    return OrganizationMonitoring.objects.get_or_create(
        organization=organization,
        type=MonitoringType.WATER_LEVEL,
        defaults=DEFAULT_MONITORING_VALUES,
    )
