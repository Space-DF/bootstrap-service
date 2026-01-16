from django.urls import path

from apps.organization.views import OrganizationView

app_name = "organization"

urlpatterns = [
    path("organizations", OrganizationView.as_view(), name="organization"),
]
