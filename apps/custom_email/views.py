from common.pagination.base_pagination import BasePagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from apps.custom_email.models import OrganizationEmail
from apps.custom_email.serializers import OrganizationEmailSerializer
from utils.views import OrganizationListAPIView


class ListCustomEmailView(OrganizationListAPIView):
    serializer_class = OrganizationEmailSerializer
    queryset = OrganizationEmail.objects.all()
    organization_field = "organization"
    pagination_class = BasePagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering = ["-created_at"]
