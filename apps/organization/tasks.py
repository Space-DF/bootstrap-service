import logging
from operator import itemgetter

from common.celery import constants
from common.celery.tasks import task
from django.db import transaction
from django.db.models import BooleanField, Case, F, IntegerField, Value, When
from django.db.models.functions import Greatest
from django.db.utils import ProgrammingError

from apps.organization.models import Organization

logger = logging.getLogger(__name__)


@task(
    name=f"spacedf.tasks.{constants.CONSOLE_SERVICE_ADD_OR_REMOVE_SPACE}",
    autoretry_for=(ProgrammingError,),
    retry_backoff=2,
    max_retries=3,
)
@transaction.atomic
def add_or_remove_space(**kwargs):
    slug_name, action_type = itemgetter("slug_name", "type")(kwargs)
    value = Case(
        When(Value(action_type == "add", output_field=BooleanField()), then=Value(1)),
        When(
            Value(action_type == "remove", output_field=BooleanField()),
            then=Value(-1),
        ),
        default=Value(0),
        output_field=IntegerField(),
    )

    Organization.objects.filter(slug_name=slug_name).update(
        total_spaces=Greatest(F("total_spaces") + value, Value(1)),
    )
