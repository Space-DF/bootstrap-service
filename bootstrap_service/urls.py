"""bootstrap_service URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.db import connection
from django.http import HttpResponse
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="SPACEDF BOOTSTRAP API",
        default_version="v1",
        terms_of_service="https://spacedf.com/terms-of-service",
        contact=openapi.Contact(email="hello@df.technology"),
        license=openapi.License(name="Apache 2.0"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)


def health_check(_):
    if not connection.ensure_connection():
        return HttpResponse("OK")
    return HttpResponse(status=500)


urlpatterns = [
    # docs UI
    re_path(
        r"^bootstrap/docs/$",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    # health
    path("bootstrap/api/health", health_check),
    # admin
    path("bootstrap/admin/", admin.site.urls),
    # apis
    path("api/bootstrap/", include("apps.authentication.urls")),
    path("api/", include("apps.organization.urls")),
]
