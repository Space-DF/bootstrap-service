from common.models.base_model import BaseModel
from common.models.synchronous_model import SynchronousTenantModel
from django.contrib.postgres.fields import ArrayField
from django.db import models

from apps.authentication.models import RootUser
from apps.organization_roles.constants import OrganizationPermission


class OrganizationPolicy(BaseModel):
    name = models.CharField(max_length=256)
    description = models.TextField()
    tags = ArrayField(models.CharField(max_length=256))
    permissions = ArrayField(
        models.CharField(max_length=256, choices=OrganizationPermission.choices)
    )
    organization = models.ForeignKey(
        "organization.Organization", on_delete=models.CASCADE, default=None
    )


class OrganizationRole(BaseModel, SynchronousTenantModel):
    name = models.CharField(max_length=256)
    policies = models.ManyToManyField(OrganizationPolicy)
    organization = models.ForeignKey(
        "organization.Organization",
        on_delete=models.CASCADE,
        related_name="organization_role",
    )


class OrganizationRoleUser(BaseModel):
    organization_role = models.ForeignKey(
        OrganizationRole,
        related_name="organization_role_user",
        on_delete=models.CASCADE,
    )
    root_user = models.ForeignKey(
        RootUser,
        related_name="organization_role_user",
        on_delete=models.CASCADE,
    )
