from django.urls import path

from apps.organization_setting.views import UpdateOrganizationSettingView

app_name = "organization_setting"

urlpatterns = [
    path(
        "organizations/settings",
        UpdateOrganizationSettingView.as_view(),
        name="organization-settings-update",
    ),
]
