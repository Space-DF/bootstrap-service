from rest_framework import status
from rest_framework.response import Response

from apps.organization.models import Organization


def resolve_organization_from_header(request):
    slug_name = request.headers.get("X-Organization")
    if not slug_name:
        return None, Response(
            {"detail": "X-Organization header is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        return Organization.objects.get(slug_name=slug_name), None
    except Organization.DoesNotExist:
        return None, Response(
            {"detail": f"Organization '{slug_name}' not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
