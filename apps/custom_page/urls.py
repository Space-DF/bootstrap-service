from django.urls import path

from apps.custom_page.views import ListCustomPageView

app_name = "custom_page"

urlpatterns = [
    path("custom-pages", ListCustomPageView.as_view(), name="custom-pages-list"),
]
