from rest_framework import mixins
from rest_framework.exceptions import ParseError
from rest_framework.generics import GenericAPIView

from apps.organization.models import Organization


class OrganizationAPIView(GenericAPIView):
    organization_field = None

    def get_queryset(self):
        queryset = super().get_queryset()

        if getattr(self, "swagger_fake_view", False):
            return queryset

        if self.organization_field is None:
            raise Exception(
                "'%s' should either include a `organization_field` attribute, or override the `get_queryset()` method."
                % self.__class__.__name__
            )

        organization_slug_name = self.request.headers.get("X-Organization", None)
        if organization_slug_name is None:
            raise ParseError("X-Organization header is required")

        filters = {
            f"{self.organization_field}__slug_name": organization_slug_name,
            f"{self.organization_field}__is_active": True,
        }

        return queryset.filter(**filters)

    def create_with_organization(self, serializer):
        if "__" not in self.organization_field:
            organization = Organization.objects.get(
                slug_name=self.request.headers.get("X-Organization")
            )
            return serializer.save(**{self.organization_field: organization})

        return serializer.save()


class OrganizationListAPIView(mixins.ListModelMixin, OrganizationAPIView):
    """
    Concrete view for listing a queryset of organization.
    """

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class OrganizationRetrieveAPIView(mixins.RetrieveModelMixin, OrganizationAPIView):
    """
    Concrete view for retrieving a model instance of organization.
    """

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
