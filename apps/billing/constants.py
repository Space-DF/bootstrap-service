from django.db import models


class CurrencyType(models.TextChoices):
    USD = "USD"
    VND = "VND"


class BillingCycle(models.TextChoices):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class FeatureValueType(models.TextChoices):
    BOOLEAN = "boolean"
    LIMIT = "limit"
    QUOTA = "quota"


class UsageType(models.TextChoices):
    RESOURCE = "resource"
    PERIOD = "period"