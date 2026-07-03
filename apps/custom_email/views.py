from common.pagination.base_pagination import BasePagination
from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from apps.custom_email.models import OrganizationEmail
from apps.custom_email.serializers import OrganizationEmailSerializer
from apps.organization_setting.models import OrganizationTheme
from utils.views import OrganizationListAPIView


class ListCustomEmailView(OrganizationListAPIView):
    serializer_class = OrganizationEmailSerializer
    queryset = OrganizationEmail.objects.select_related(
        "organization",
        "organization__organization_settings",
    ).prefetch_related(
        Prefetch(
            "organization__organization_settings__themes",
            queryset=OrganizationTheme.objects.all(),
        )
    )
    organization_field = "organization"
    pagination_class = BasePagination
    filterset_fields = ["email_type"]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering = ["-created_at"]
