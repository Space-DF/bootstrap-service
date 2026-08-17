from rest_framework import generics, permissions

from apps.organization_monitoring.models import OrganizationMonitoring
from apps.organization_monitoring.serializers import OrganizationMonitoringSerializer
from utils.views import (
    OrganizationContextMixin,
    OrganizationListCreateAPIView,
    OrganizationRetrieveUpdateDestroyAPIView,
)


class MonitoringListCreateView(OrganizationListCreateAPIView):
    model = OrganizationMonitoring
    serializer_class = OrganizationMonitoringSerializer
    queryset = OrganizationMonitoring.objects.select_related("organization")
    organization_field = "organization"


class MonitoringDetailView(OrganizationRetrieveUpdateDestroyAPIView):
    model = OrganizationMonitoring
    serializer_class = OrganizationMonitoringSerializer
    queryset = OrganizationMonitoring.objects.select_related("organization")
    organization_field = "organization"


class UserMonitoringListView(OrganizationContextMixin, generics.ListAPIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    serializer_class = OrganizationMonitoringSerializer
    queryset = OrganizationMonitoring.objects.select_related("organization")


class UserMonitoringDetailView(
    OrganizationContextMixin,
    generics.RetrieveAPIView,
):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    serializer_class = OrganizationMonitoringSerializer
    queryset = OrganizationMonitoring.objects.select_related("organization")
