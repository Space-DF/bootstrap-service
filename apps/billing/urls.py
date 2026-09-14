from django.urls import path

from apps.billing.views import QuotaView, ReleaseQuotaView, ReserveQuotaView

app_name = "billing"

urlpatterns = [
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
