from rest_framework import mixins
from rest_framework.exceptions import ParseError
from rest_framework.generics import GenericAPIView

from apps.organization.models import Organization


class OrganizationContextMixin:
    organization_field = "organization"

    def get_organization_slug(self):
        headers = self.request.headers
        slug_name = headers.get("X-Organization") or headers.get("X-Org")
        if slug_name:
            return slug_name

        tenant = getattr(self.request, "tenant", None)
        slug_name = getattr(tenant, "slug_name", None)
        if slug_name:
            return slug_name

        hostname = self.request.get_host().split(":", 1)[0]
        parts = hostname.split(".")
        if len(parts) < 2:
            return None

        slug_name = parts[0]
        if slug_name in {"www", "api"}:
            return None
        return slug_name

    def get_organization(self):
        slug_name = self.get_organization_slug()
        if not slug_name:
            raise ParseError("Organization context is required")

        try:
            return Organization.objects.get(slug_name=slug_name, is_active=True)
        except Organization.DoesNotExist as exc:
            raise ParseError(f"Organization '{slug_name}' not found") from exc

    def get_queryset(self):
        queryset = super().get_queryset()

        if getattr(self, "swagger_fake_view", False):
            return queryset

        return queryset.filter(**{self.organization_field: self.get_organization()})


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


class OrganizationCreateAPIView(mixins.CreateModelMixin, OrganizationAPIView):
    """
    Concrete view for creating a model instance of organization.
    """

    def perform_create(self, serializer):
        self.create_with_organization(serializer)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


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


class OrganizationDestroyAPIView(mixins.DestroyModelMixin, OrganizationAPIView):
    """
    Concrete view for deleting a model instance of organization.
    """

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class OrganizationUpdateAPIView(mixins.UpdateModelMixin, OrganizationAPIView):
    """
    Concrete view for updating a model instance of organization.
    """

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class OrganizationListCreateAPIView(
    mixins.ListModelMixin, mixins.CreateModelMixin, OrganizationAPIView
):
    """
    Concrete view for listing a queryset or creating a model instance of organization.
    """

    def perform_create(self, serializer):
        self.create_with_organization(serializer)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class OrganizationRetrieveUpdateAPIView(
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, OrganizationAPIView
):
    """
    Concrete view for retrieving, updating a model instance of organization.
    """

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class OrganizationRetrieveDestroyAPIView(
    mixins.RetrieveModelMixin, mixins.DestroyModelMixin, OrganizationAPIView
):
    """
    Concrete view for retrieving or deleting a model instance of organization.
    """

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class OrganizationRetrieveUpdateDestroyAPIView(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    OrganizationAPIView,
):
    """
    Concrete view for retrieving, updating or deleting a model instance of organization.
    """

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
