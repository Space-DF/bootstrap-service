from django.urls import path

from apps.organization.views import CheckOrganizationView, OrganizationView

app_name = "organization"

urlpatterns = [
    path("organizations", OrganizationView.as_view(), name="organization"),
    path(
        "organizations/check/<str:slug_name>",
        CheckOrganizationView.as_view(),
        name="check-organization",
    ),
]
