from common.pagination.base_pagination import BasePagination
from rest_framework import generics
from rest_framework.filters import OrderingFilter

from apps.billing.models import Plan
from apps.billing.serializers import PlanSerializer


class PlanListView(generics.ListAPIView):
    """List active subscription plans with their feature definitions."""

    serializer_class = PlanSerializer
    pagination_class = BasePagination
    filter_backends = [OrderingFilter]
    ordering = ["price"]
    queryset = Plan.objects.filter(is_active=True).prefetch_related(
        "plan_features__feature"
    )
