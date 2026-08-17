from django.db import models


class PlanCodeType:
    # Plan code used as the default when provisioning a new organization.
    FREE = "free"
    PRO = "pro"


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


BILLING_CYCLE_DAYS = {
    BillingCycle.MONTHLY: 30,
    BillingCycle.YEARLY: 365,
}
