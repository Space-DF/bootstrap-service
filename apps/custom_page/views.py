from common.apps.billing.mixins import QuotaMixin
from common.pagination.base_pagination import BasePagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from apps.billing.quotas import WhitelabelQuota
from apps.custom_page.models import CustomPage
from apps.custom_page.serializers import CustomPageSerializer
from utils.views import OrganizationListAPIView


class ListCustomPageView(QuotaMixin, OrganizationListAPIView):
    serializer_class = CustomPageSerializer
    queryset = CustomPage.objects.select_related("organization").all()
    organization_field = "organization"
    pagination_class = BasePagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering = ["-created_at"]
    quota_classes = [WhitelabelQuota]
