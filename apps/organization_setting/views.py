from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response

from apps.organization.models import Organization
from apps.organization_setting.models import OrganizationSetting
from apps.organization_setting.serializers import (
    OrganizationConfigSerializer,
    UpdateOrganizationSettingSerializer,
)


class UpdateOrganizationSettingView(generics.UpdateAPIView):
    serializer_class = UpdateOrganizationSettingSerializer
    queryset = OrganizationSetting.objects.select_related(
        "organization"
    ).prefetch_related(
        "themes",
        "organization__organization_custom_emails",
        "organization__organization_custom_page",
    )

    def get_object(self):
        organization = get_object_or_404(
            Organization,
            slug_name=self.request.headers.get("X-Organization"),
            is_active=True,
        )
        return get_object_or_404(self.get_queryset(), organization=organization)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()
        fresh_instance = self.get_queryset().get(pk=updated_instance.pk)
        response_serializer = OrganizationConfigSerializer(
            fresh_instance,
            context=self.get_serializer_context(),
        )
        return Response(response_serializer.data)
