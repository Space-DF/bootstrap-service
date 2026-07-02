from django.urls import path

from apps.custom_email.views import ListCustomEmailView

app_name = "custom_email"

urlpatterns = [
    path("custom-emails", ListCustomEmailView.as_view(), name="custom-emails-list"),
]
