from operator import itemgetter
from typing import Literal

import requests
from common.apps.refresh_tokens.services import create_jwt_tokens
from django.conf import settings
from django.core.cache import cache
from django.template.loader import render_to_string
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.authentication.models import RootUser
from apps.organization.models import Organization
from apps.organization_roles.models import OrganizationRoleUser


def create_organization_access_token(user_id, access_token):
    organization_roles_cache = cache.get(f"organization_roles_{user_id}")
    if organization_roles_cache:
        access_token["organization_roles"] = organization_roles_cache
        return access_token

    # query role per organization
    org_role_users = (
        OrganizationRoleUser.objects.filter(
            root_user_id=user_id, organization_role__organization__is_active=True
        )
        .select_related("organization_role__organization")
        .order_by("organization_role__organization_id")
        .distinct("organization_role__organization_id")
    )

    # build dict organization_slug -> role_name
    organization_roles_dict = {}
    for org_role_user in org_role_users:
        org_slug = str(org_role_user.organization_role.organization.slug_name)
        role_name = str(org_role_user.organization_role.name)
        organization_roles_dict[org_slug] = role_name

    cache.set(
        f"organization_roles_{user_id}",
        organization_roles_dict,
        timeout=60 * 60 * 24,
    )

    # update access token
    access_token["organization_roles"] = organization_roles_dict
    return access_token


def create_organization_jwt_tokens(user, organization_slug, issuer=None, **kwargs):
    refresh_token, access_token = create_jwt_tokens(user, issuer, **kwargs)

    if organization_slug:
        access_token = create_organization_access_token(user.id, access_token)
    return refresh_token, access_token


def handle_access_token(access_token, provider: Literal["GOOGLE"]):
    info_url = settings.OAUTH_CLIENTS[provider]["INFO_URL"]

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(url=info_url, headers=headers, timeout=10)
    response.raise_for_status()
    user_info_dict = response.json()
    given_name, family_name, email = itemgetter("given_name", "family_name", "email")(
        user_info_dict
    )
    root_user, is_created = RootUser.objects.get_or_create(
        email=email,
    )
    if is_created:
        root_user.first_name = given_name
        root_user.last_name = family_name
        root_user.save()

    default_organization = Organization.objects.filter(
        organizationpolicy__organizationrole__organization_role_user__root_user=root_user,
    ).first()
    default_organization_slug = (
        default_organization.slug_name if default_organization else None
    )

    refresh, access = create_organization_jwt_tokens(
        root_user, organization_slug=default_organization_slug
    )
    return Response(
        status=status.HTTP_200_OK,
        data={
            "refresh": str(refresh),
            "access": str(access),
            "default_organization": default_organization_slug,
        },
    )


def render_email_format(template, data):
    try:
        html_message = render_to_string(
            template,
            data,
        )
        return html_message
    except Exception as e:
        raise ValidationError({"error": f"Error: {e}"})
