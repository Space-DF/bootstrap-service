from django.urls import path

from apps.contact_sales.views import ContactSalesStatusView, ContactSalesView

app_name = "contact_sales"

urlpatterns = [
    path("contact-sales", ContactSalesView.as_view(), name="contact-sales"),
    path(
        "contact-sales/status",
        ContactSalesStatusView.as_view(),
        name="contact-sales-status",
    ),
]
