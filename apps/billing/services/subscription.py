import logging
from datetime import timedelta

from django.utils import timezone

from apps.billing.constants import BILLING_CYCLE_DAYS, BillingCycle, PlanCodeType
from apps.billing.models import PlanItem, Subscription

logger = logging.getLogger(__name__)


def _chargebee_item_price_id(plan_item):
    return f"{plan_item.plan.code}_{plan_item.billing_cycle}"


def create_default_subscription(organization, owner=None):
    """Create the default Free subscription for a newly-created organization.

    Idempotent-safe: returns None (without raising) if the Free plan has not
    been seeded yet, so organization creation never fails because of billing
    setup.

    Args:
        organization: The newly-created Organization.
    """
    plan_item = (
        PlanItem.objects.select_related("plan")
        .filter(
            plan__code=PlanCodeType.FREE,
            billing_cycle=BillingCycle.MONTHLY,
            is_active=True,
        )
        .first()
    )
    if plan_item is None:
        logger.warning(
            "Default plan item '%s' not found, skipping subscription for org %s. "
            "Run the billing seed migration.",
            PlanCodeType.FREE,
            organization.slug_name,
        )
        return None

    now = timezone.now()
    duration_days = BILLING_CYCLE_DAYS.get(plan_item.billing_cycle, 30)
    period_end = now + timedelta(days=duration_days)

    subscription = Subscription.objects.create(
        organization=organization,
        plan_item=plan_item,
        period_start=now,
        period_end=period_end,
    )

    return subscription
