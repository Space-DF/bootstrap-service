from django.db import models


class MonitoringType(models.TextChoices):
    WATER_LEVEL = "water_level"
