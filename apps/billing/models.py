from common.models.base_model import BaseModel
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.billing.constants import (
    BillingCycle,
    CurrencyType,
    FeatureValueType,
    UsageType,
)
from apps.organization.models import Organization


class Plan(BaseModel):
    name = models.CharField(max_length=256)
    code = models.CharField(max_length=64, unique=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=256, blank=True, default="")
    support = models.TextField(blank=True)
    currency = models.CharField(
        max_length=8, choices=CurrencyType.choices, default=CurrencyType.USD
    )
    discount = models.IntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    billing_cycle = models.CharField(
        max_length=16, choices=BillingCycle.choices, default=BillingCycle.MONTHLY
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "plans"


class Feature(BaseModel):
    code = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=256)
    description = models.TextField(blank=True)
    value_type = models.CharField(max_length=16, choices=FeatureValueType.choices)

    class Meta:
        db_table = "features"


class PlanFeature(BaseModel):
    plan = models.ForeignKey(
        Plan, on_delete=models.CASCADE, related_name="plan_features"
    )
    feature = models.ForeignKey(
        Feature, on_delete=models.CASCADE, related_name="plan_features"
    )
    enabled = models.BooleanField(default=True)
    limit_value = models.IntegerField(
        null=True, blank=True, validators=[MinValueValidator(0)]
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "plan_features"
        constraints = [
            models.UniqueConstraint(
                fields=["plan", "feature"], name="unique_plan_feature"
            ),
        ]


class Subscription(BaseModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    plan = models.ForeignKey(
        Plan, on_delete=models.CASCADE, related_name="subscriptions"
    )
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()

    class Meta:
        db_table = "subscriptions"
        constraints = [
            models.CheckConstraint(
                check=models.Q(period_end__gt=models.F("period_start")),
                name="subscription_period_end_after_period_start",
            ),
        ]


class FeatureUsage(BaseModel):
    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name="feature_usages"
    )
    feature = models.ForeignKey(
        Feature, on_delete=models.CASCADE, related_name="feature_usages"
    )
    usage_type = models.CharField(max_length=16, choices=UsageType.choices)
    used_value = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
    billing_period = models.DateField()

    class Meta:
        db_table = "feature_usages"
