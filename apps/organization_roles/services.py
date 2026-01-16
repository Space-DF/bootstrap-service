from django.contrib.auth import get_user_model
from django.core.cache import cache

from apps.organization_roles.constants import OrganizationPermission
from apps.organization_roles.models import OrganizationPolicy, OrganizationRole

User = get_user_model()


default_policies = [
    {
        "name": "Administrator access",
        "description": "Provides full access to services and resources",
        "tags": ["administrator"],
        "permissions": [permission.value for permission in OrganizationPermission],
    },
    {
        "name": "Organization full access",
        "description": "Grants full access to Organization resources and access to related services",
        "tags": ["organization", "full-access"],
        "permissions": [
            OrganizationPermission.UPDATE_ORGANIZATION,
            OrganizationPermission.DELETE_ORGANIZATION,
        ],
    },
    {
        "name": "Organization's Role read-only access",
        "description": "Provide read only access to Organization's Role services",
        "tags": ["organization-role", "read-only"],
        "permissions": [
            OrganizationPermission.READ_ORGANIZATION_ROLE,
        ],
    },
    {
        "name": "Organization's Role edit-only access",
        "description": "Provide edit only access to Organization's Role services",
        "tags": ["organization-role", "edit-only"],
        "permissions": [
            OrganizationPermission.UPDATE_ORGANIZATION_ROLE,
        ],
    },
    {
        "name": "Organization's Role full access",
        "description": "Grants full access to Organization's Role resources and access to related services",
        "tags": ["organization-role", "full-access"],
        "permissions": [
            OrganizationPermission.READ_ORGANIZATION_ROLE,
            OrganizationPermission.CREATE_ORGANIZATION_ROLE,
            OrganizationPermission.UPDATE_ORGANIZATION_ROLE,
            OrganizationPermission.DELETE_ORGANIZATION_ROLE,
        ],
    },
    {
        "name": "Organization's Member read-only access",
        "description": "Provide read only access to Organization's Member services",
        "tags": ["organization-member", "read-only"],
        "permissions": [
            OrganizationPermission.READ_ORGANIZATION_MEMBER,
        ],
    },
    {
        "name": "Organization's Member edit-only access",
        "description": "Provide edit only access to Organization's Member services",
        "tags": ["organization-member", "edit-only"],
        "permissions": [
            OrganizationPermission.UPDATE_ORGANIZATION_MEMBER_ROLE,
        ],
    },
    {
        "name": "Organization's Member full access",
        "description": "Grants full access to Organization's Member resources and access to related services",
        "tags": ["organization-member", "full-access"],
        "permissions": [
            OrganizationPermission.READ_ORGANIZATION_MEMBER,
            OrganizationPermission.INVITE_ORGANIZATION_MEMBER,
            OrganizationPermission.UPDATE_ORGANIZATION_MEMBER_ROLE,
            OrganizationPermission.REMOVE_ORGANIZATION_MEMBER,
        ],
    },
    {
        "name": "Organization's Device read-only access",
        "description": "Provide read only access to Organization's Device services",
        "tags": ["organization-device", "read-only"],
        "permissions": [
            OrganizationPermission.READ_ORGANIZATION_DEVICE,
        ],
    },
    {
        "name": "Organization's Device edit-only access",
        "description": "Provide edit only access to Organization's Device services",
        "tags": ["organization-device", "edit-only"],
        "permissions": [
            OrganizationPermission.UPDATE_ORGANIZATION_DEVICE,
        ],
    },
    {
        "name": "Organization's Device full access",
        "description": "Grants full access to Organization's Device resources and access to related services",
        "tags": ["organization-device", "full-access"],
        "permissions": [
            OrganizationPermission.READ_ORGANIZATION_DEVICE,
            OrganizationPermission.CREATE_ORGANIZATION_DEVICE,
            OrganizationPermission.UPDATE_ORGANIZATION_DEVICE,
            OrganizationPermission.DELETE_ORGANIZATION_DEVICE,
        ],
    },
]


def create_default_policies(organization):
    organization_policies = []
    for policy in default_policies:
        organization_policy = OrganizationPolicy(**policy, organization=organization)
        organization_policy.save()
        organization_policies.append(organization_policy.pk)
    return organization_policies


def create_default_organization_role_by_policy_tag(name, tag, organization):
    policies = OrganizationPolicy.objects.filter(
        tags__icontains=tag, organization=organization
    ).all()
    organization_role = OrganizationRole(name=name, organization=organization)
    organization_role.save()
    organization_role.policies.set([policy.pk for policy in policies])
    organization_role.save()
    return organization_role


def clear_user_permission_cache(user_id):
    if user_id:
        cache_key = f"organization_roles_{user_id}"
        if cache.get(cache_key):
            cache.delete(cache_key)
