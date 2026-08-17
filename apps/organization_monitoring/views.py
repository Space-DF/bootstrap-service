from apps.organization_monitoring.models import OrganizationMonitoring
from apps.organization_monitoring.serializers import OrganizationMonitoringSerializer
from utils.views import (
    OrganizationListCreateAPIView,
    OrganizationRetrieveUpdateDestroyAPIView,
)


class OrganizationMonitoringListCreateView(OrganizationListCreateAPIView):
    model = OrganizationMonitoring
    serializer_class = OrganizationMonitoringSerializer
    queryset = OrganizationMonitoring.objects.select_related("organization")
    organization_field = "organization"


class OrganizationMonitoringDetailView(OrganizationRetrieveUpdateDestroyAPIView):
    model = OrganizationMonitoring
    serializer_class = OrganizationMonitoringSerializer
    queryset = OrganizationMonitoring.objects.select_related("organization")
    organization_field = "organization"
