from django.urls import path

from apps.organization_monitoring.views import (
    MonitoringDetailView,
    MonitoringListCreateView,
    UserMonitoringDetailView,
    UserMonitoringListView,
)

app_name = "organization_monitoring"

urlpatterns = [
    path(
        "organizations/monitoring",
        UserMonitoringListView.as_view(),
        name="organization-monitoring-list",
    ),
    path(
        "organizations/monitoring/<uuid:pk>",
        UserMonitoringDetailView.as_view(),
        name="organization-monitoring-detail",
    ),
    path(
        "bootstrap/organizations/monitoring",
        MonitoringListCreateView.as_view(),
        name="bootstrap-organization-monitoring-list",
    ),
    path(
        "bootstrap/organizations/monitoring/<uuid:pk>",
        MonitoringDetailView.as_view(),
        name="bootstrap-organization-monitoring-detail",
    ),
]
