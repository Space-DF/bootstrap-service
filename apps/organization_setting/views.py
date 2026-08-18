from common.apps.billing.mixins import QuotaMixin
from django.shortcuts import get_object_or_404

from apps.billing.quotas import WhitelabelQuota
from apps.organization.models import Organization
from apps.organization_setting.models import OrganizationSetting
from apps.organization_setting.serializers import UpdateOrganizationSettingSerializer
from utils.views import OrganizationUpdateAPIView


class UpdateOrganizationSettingView(QuotaMixin, OrganizationUpdateAPIView):
    serializer_class = UpdateOrganizationSettingSerializer
    queryset = OrganizationSetting.objects.select_related(
        "organization"
    ).prefetch_related("themes")
    organization_field = "organization"
    quota_classes = [WhitelabelQuota]

    def get_object(self):
        organization = get_object_or_404(
            Organization,
            slug_name=self.request.headers.get("X-Organization"),
            is_active=True,
        )
        return get_object_or_404(self.get_queryset(), organization=organization)
