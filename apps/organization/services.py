from random import SystemRandom

from django.conf import settings
from django.db.models import CharField, F, OuterRef, Value
from django.db.models.functions import Cast, Coalesce, Concat, NullIf, Trim

from apps.organization.constants import UNICODE_ASCII_CHARACTER_SET
from apps.organization_roles.constants import OrganizationRoleType
from apps.organization_roles.models import OrganizationRoleUser


def get_owner_name_query_set():
    return (
        OrganizationRoleUser.objects.filter(
            organization_role__organization_id=OuterRef("pk"),
            organization_role__name__iexact=OrganizationRoleType.OWNER_ROLE,
        )
        .order_by("id")
        .annotate(
            display=Coalesce(
                NullIf(
                    Trim(
                        Concat(
                            Coalesce(F("root_user__first_name"), Value("")),
                            Value(" "),
                            Coalesce(F("root_user__last_name"), Value("")),
                        )
                    ),
                    Value(""),
                ),
                Cast(F("root_user__email"), CharField()),
            )
        )
        .values("display")[:1]
    )


def generate_client_secret():
    """
    Generate a suitable client secret
    """
    length = settings.CLIENT_SECRET_GENERATOR_LENGTH
    rand = SystemRandom()
    return "".join(rand.choice(UNICODE_ASCII_CHARACTER_SET) for _ in range(length))
