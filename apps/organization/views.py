from common.pagination.base_pagination import BasePagination
from django.db.models import CharField, Count, Subquery
from django.shortcuts import get_object_or_404
from rest_framework.filters import OrderingFilter, SearchFilter

from apps.organization.models import Organization
from apps.organization.serializers import OrganizationSerializer
from apps.organization.services import get_owner_name_query_set
from utils.views import OrganizationRetrieveAPIView


class OrganizationView(OrganizationRetrieveAPIView):
    model = Organization
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    pagination_class = BasePagination
    filter_backends = [OrderingFilter, SearchFilter]
    ordering_fields = ["created_at"]
    search_fields = ["name"]

    def get_object(self):
        organization_slug = self.request.headers.get("X-Organization", None)
        if not organization_slug:
            return None
        return get_object_or_404(Organization, slug_name=organization_slug)

    def get_queryset(self):
        user_id = self.request.headers.get("X-User-ID", None)
        if not user_id:
            return self.queryset.none()

        return (
            Organization.objects.filter(
                organization_role__organization_role_user__root_user_id=user_id
            )
            .annotate(
                created_by=Subquery(
                    get_owner_name_query_set(), output_field=CharField()
                ),
                total_member=Count(
                    "organization_role__organization_role_user", distinct=True
                ),
            )
            .distinct()
        )
