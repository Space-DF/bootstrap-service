from common.pagination.base_pagination import BasePagination
from django.db.models import Min, Prefetch
from rest_framework import generics
from rest_framework.filters import OrderingFilter

from apps.billing.models import Plan, PlanItem
from apps.billing.serializers import PlanSerializer


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
