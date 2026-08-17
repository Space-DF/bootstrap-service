from django.urls import path

from apps.organization_monitoring.views import (
    OrganizationMonitoringDetailView,
    OrganizationMonitoringListCreateView,
)

app_name = "organization_monitoring"

urlpatterns = [
    path(
        "organizations/monitoring",
        OrganizationMonitoringListCreateView.as_view(),
        name="organization-monitoring-list",
    ),
    path(
        "organizations/monitoring/<uuid:pk>",
        OrganizationMonitoringDetailView.as_view(),
        name="organization-monitoring-detail",
    ),
]
