import logging

from common.models.base_model import BaseModel
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

logger = logging.getLogger(__name__)


def no_underscore_validator(value):
    if "_" in value:
        raise ValidationError("Slug cannot contain underscores (_).")


class Organization(BaseModel):
    name = models.CharField(max_length=256)
    logo = models.CharField(max_length=256)
    slug_name = models.SlugField(
        max_length=64, unique=True, validators=[no_underscore_validator]
    )
    is_active = models.BooleanField(default=True)
    total_spaces = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    # RabbitMQ provisioning fields
    rabbitmq_vhost = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Assigned RabbitMQ pooled vhost",
    )
    rabbitmq_provisioned_at = models.DateTimeField(
        blank=True, null=True, help_text="When RabbitMQ resources were provisioned"
    )
