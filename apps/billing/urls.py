from django.urls import path

from apps.billing.views import (
    PlanDetailView,
    PlanListView,
    QuotaView,
    ReleaseQuotaView,
    ReserveQuotaView,
)

app_name = "billing"

urlpatterns = [
    path("plans", PlanListView.as_view(), name="plans"),
    path("plans/<str:code>", PlanDetailView.as_view(), name="plan-detail"),
    path(
        "billing/internal/quota/reserve",
        ReserveQuotaView.as_view(),
        name="reserve-quota",
    ),
    path(
        "billing/internal/quota/release",
        ReleaseQuotaView.as_view(),
        name="release-quota",
    ),
    path("billing/quota", QuotaView.as_view(), name="quota"),
]
