from django.urls import path

from apps.billing.views import PlanListView

app_name = "billing"

urlpatterns = [
    path("plans", PlanListView.as_view(), name="plans"),
]
