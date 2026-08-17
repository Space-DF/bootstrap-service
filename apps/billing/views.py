from common.pagination.base_pagination import BasePagination
from django.db.models import Min, Prefetch
from rest_framework import generics, permissions, status
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from apps.billing.models import Plan, PlanItem
from apps.billing.serializers import (
    PlanWithFeaturesSerializer,
    ReserveQuotaSerializer,
    ViewQuotaSerializer,
)
from apps.billing.services.subscription import (
    get_quotas,
    release_quotas,
    reserve_quotas,
)


class PlanListView(generics.ListAPIView):
    """List active subscription plans with their feature definitions."""

    serializer_class = PlanWithFeaturesSerializer
    pagination_class = BasePagination
    filter_backends = [OrderingFilter]
    ordering = ["price"]
    ordering_fields = ["code", "name", "price"]
    queryset = (
        Plan.objects.filter(plan_items__is_active=True)
        .annotate(price=Min("plan_items__price"))
        .prefetch_related(
            Prefetch(
                "plan_items",
                queryset=PlanItem.objects.filter(is_active=True).order_by("price"),
            ),
            "plan_features__feature",
        )
    )


class PlanDetailView(generics.RetrieveAPIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    serializer_class = PlanWithFeaturesSerializer
    lookup_field = "code"
    queryset = (
        Plan.objects.filter(plan_items__is_active=True)
        .distinct()
        .prefetch_related(
            Prefetch(
                "plan_items",
                queryset=PlanItem.objects.filter(is_active=True).order_by("price"),
            ),
            "plan_features__feature",
        )
    )


class ReserveQuotaView(generics.GenericAPIView):
    """Internal endpoint — reserves quota for a feature.

    Called by other services before creating a billable resource.

    Request body::
        {
            "organization": "<slug_name>",
            "feature": ["<code>"],
            "amount": 1,
            "scope_type": "user",
            "scope_id": "<uuid>"
        }

    Returns 200 if reserved, 403 if quota exceeded.
    """

    swagger_schema = None
    serializer_class = ReserveQuotaSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        slug_name = serializer.validated_data["organization"]
        feature_codes = serializer.validated_data["feature"]
        amount = serializer.validated_data["amount"]
        scope_type = serializer.validated_data.get("scope_type")
        scope_id = serializer.validated_data.get("scope_id")

        from apps.organization.models import Organization

        try:
            organization = Organization.objects.get(slug_name=slug_name)
        except Organization.DoesNotExist:
            return Response(
                {"detail": f"Organization '{slug_name}' not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        reserved, error = reserve_quotas(
            organization,
            feature_codes,
            amount,
            scope_type,
            scope_id,
        )
        if reserved:
            return Response({"status": "reserved"})
        return Response({"detail": error}, status=status.HTTP_403_FORBIDDEN)


class ReleaseQuotaView(generics.GenericAPIView):
    """Internal endpoint — releases previously reserve quota.

    Called when resource creation failed after a successful reserve.
    Always returns 200.

    Request body::
        {
            "organization": "<slug_name>",
            "feature": ["<code>"],
            "amount": 1,
            "scope_type": "user",
            "scope_id": "<uuid>"
        }
    """

    swagger_schema = None
    serializer_class = ReserveQuotaSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        slug_name = serializer.validated_data["organization"]
        feature_codes = serializer.validated_data["feature"]
        amount = serializer.validated_data["amount"]
        scope_type = serializer.validated_data.get("scope_type")
        scope_id = serializer.validated_data.get("scope_id")

        from apps.organization.models import Organization

        try:
            organization = Organization.objects.get(slug_name=slug_name)
        except Organization.DoesNotExist:
            return Response(
                {"detail": f"Organization '{slug_name}' not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        release_quotas(organization, feature_codes, amount, scope_type, scope_id)
        return Response({"status": "released"})


class QuotaView(generics.GenericAPIView):
    """Internal endpoint — views quota for a feature.

    Request body::
        {
            "organization": "<slug_name>",
            "feature": ["<code>"],
            "scope_type": "user",
            "scope_id": "<uuid>"
        }
    """

    serializer_class = ViewQuotaSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        slug_name = serializer.validated_data["organization"]
        feature_codes = serializer.validated_data["feature"]
        scope_type = serializer.validated_data.get("scope_type")
        scope_id = serializer.validated_data.get("scope_id")

        from apps.organization.models import Organization

        try:
            organization = Organization.objects.get(slug_name=slug_name)
        except Organization.DoesNotExist:
            return Response(
                {"detail": f"Organization '{slug_name}' not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        quotas = get_quotas(organization, feature_codes, scope_type, scope_id)
        if len(feature_codes) == 1:
            return Response({"quota": quotas[feature_codes[0]]})
        return Response({"quotas": quotas})
