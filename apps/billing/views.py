from common.pagination.base_pagination import BasePagination
from django.db.models import BooleanField, Case, Min, Prefetch, Value, When
from rest_framework import generics
from rest_framework.filters import OrderingFilter

from apps.billing.constants import PlanCodeType
from apps.billing.models import Plan, PlanItem
from apps.billing.serializers import PlanSerializer
from apps.organization.models import Organization


class PlanListView(generics.ListAPIView):
    """List active subscription plans with their feature definitions."""

    serializer_class = PlanSerializer
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

    def get_queryset(self):
        queryset = super().get_queryset()
        organization_slug = self.request.headers.get("X-Organization")
        if not organization_slug:
            return queryset

        current_plan_code = (
            Organization.objects.filter(slug_name=organization_slug)
            .values_list("subscriptions__plan_item__plan__code", flat=True)
            .order_by("-subscriptions__created_at")
            .first()
            or PlanCodeType.FREE
        )
        return queryset.annotate(
            is_current_plan=Case(
                When(code=current_plan_code, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
