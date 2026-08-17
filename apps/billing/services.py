import logging
from datetime import timedelta

from django.utils import timezone

from apps.billing.constants import BILLING_CYCLE_DAYS, PlanCodeType
from apps.billing.models import Plan, Subscription

logger = logging.getLogger(__name__)


def create_default_subscription(organization):
    """Create the default Free subscription for a newly-created organization.
    Args:
        organization: The newly-created Organization.
    """
    plan = Plan.objects.filter(code=PlanCodeType.FREE, is_active=True).first()
    if plan is None:
        logger.warning(
            "Default plan '%s' not found, skipping subscription for org %s. "
            "Run the billing seed migration.",
            PlanCodeType.FREE,
            organization.slug_name,
        )
        return None

    now = timezone.now()
    duration_days = BILLING_CYCLE_DAYS.get(plan.billing_cycle, 30)
    period_end = now + timedelta(days=duration_days)

    subscription = Subscription.objects.create(
        organization=organization,
        plan=plan,
        period_start=now,
        period_end=period_end,
    )

    return subscription
