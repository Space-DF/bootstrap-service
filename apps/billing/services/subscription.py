import logging
from datetime import timedelta

from common.celery.task_senders import send_task
from django.core.cache import cache
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.billing.constants import BILLING_CYCLE_DAYS, BillingCycle, PlanCodeType
from apps.billing.models import (
    Feature,
    FeatureUsage,
    PlanFeature,
    PlanItem,
    Subscription,
)

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


def _get_quota_meta(organization, feature_code):
    """Resolve quota metadata for an org+feature.
    Returns (subscription_id, feature_id, limit_value, is_allowed).
    """
    subscription = (
        Subscription.objects.select_related("plan_item__plan")
        .filter(organization=organization)
        .order_by("-created_at")
        .first()
    )
    if subscription is None or subscription.plan_item_id is None:
        return None, None, None, False

    feature = Feature.objects.filter(code=feature_code).first()
    if feature is None:
        return None, None, None, False

    plan_feature = PlanFeature.objects.filter(
        plan=subscription.plan_item.plan,
        feature=feature,
        enabled=True,
    ).first()
    if plan_feature is None:
        return subscription.id, feature.id, None, False

    return subscription.id, feature.id, plan_feature.limit_value, True


def reserve_quota(organization, feature_code, amount=1):
    """Atomically reserve ``amount`` of a feature for the org's current period.
    Returns ``(reserved: bool, error: str | None)``. Limited features increment
    ``FeatureUsage.used_value`` atomically. Unlimited features are allowed
    without tracking usage.
    If the org's current plan does not include the feature, returns
    ``(False, error)``.
    """
    try:
        subscription_id, feature_id, limit_value, is_allowed = _get_quota_meta(
            organization, feature_code
        )
        if not is_allowed:
            return False, f"Feature '{feature_code}' is not allowed for current plan."
        if subscription_id is None or feature_id is None:
            return False, f"Feature '{feature_code}' is not available."
        if amount == 0 or limit_value is None:
            return True, None

        with transaction.atomic():
            period = timezone.now().date().replace(day=1)
            usage, _ = FeatureUsage.objects.select_for_update().get_or_create(
                subscription_id=subscription_id,
                feature_id=feature_id,
                billing_period=period,
                defaults={
                    "usage_type": "resource",
                    "used_value": 0,
                },
            )

            if usage.used_value + amount > limit_value:
                return False, (
                    f"Quota exceeded for '{feature_code}' "
                    f"(used {usage.used_value}/{limit_value})."
                )

            usage.used_value = F("used_value") + amount
            usage.save(update_fields=["used_value"])
            return True, None
    except Exception as e:  # noqa: BLE001
        logger.error(
            "reserve_quota failed for %s/%s: %s",
            organization.slug_name,
            feature_code,
            e,
        )
        return False, "Unable to reserve quota."


def reserve_quotas(organization, feature_codes, amount=1):
    reserved_features = []

    for feature_code in feature_codes:
        reserved, error = reserve_quota(organization, feature_code, amount)
        if not reserved:
            for reserved_feature in reserved_features:
                release_quota(organization, reserved_feature, amount)
            return False, error

        if amount > 0:
            reserved_features.append(feature_code)

    return True, None


def release_quota(organization, feature_code, amount=1):
    """Release ``amount`` back to the org's quota (e.g. when create failed)."""
    slug = organization.slug_name
    try:
        subscription_id, feature_id, _, is_allowed = _get_quota_meta(
            organization, feature_code
        )
        if subscription_id is None or feature_id is None:
            return
        if not is_allowed:
            return

        with transaction.atomic():
            period = timezone.now().date().replace(day=1)
            usage = (
                FeatureUsage.objects.select_for_update()
                .filter(
                    subscription_id=subscription_id,
                    feature_id=feature_id,
                    billing_period=period,
                )
                .first()
            )
            if usage is None:
                return

            new_value = max(usage.used_value - amount, 0)
            usage.used_value = new_value
            usage.save(update_fields=["used_value"])
    except Exception as e:  # noqa: BLE001
        logger.error("release_quota failed for %s/%s: %s", slug, feature_code, e)


def release_quotas(organization, feature_codes, amount=1):
    for feature_code in feature_codes:
        release_quota(organization, feature_code, amount)


def get_quota(organization, feature_code):
    """Get quota for a feature."""
    slug = organization.slug_name
    try:
        subscription_id, feature_id, _, is_allowed = _get_quota_meta(
            organization, feature_code
        )
        if subscription_id is None or feature_id is None or not is_allowed:
            return 0

        period = timezone.now().date().replace(day=1)
        usage = FeatureUsage.objects.filter(
            subscription_id=subscription_id,
            feature_id=feature_id,
            billing_period=period,
        ).first()
        if usage is None:
            return 0
        return usage.used_value
    except Exception as e:  # noqa: BLE001
        logger.error("get_quota failed for %s/%s: %s", slug, feature_code, e)
        return 0


def get_quotas(organization, feature_codes):
    return {
        feature_code: get_quota(organization, feature_code)
        for feature_code in feature_codes
    }


def _get_free_plan_limits():
    """Cached Free plan limits dict — queried once per hour."""
    cache_key = "billing:free_plan_limits"
    limits = cache.get(cache_key)
    if limits is not None:
        return limits

    from apps.billing.models import Plan, PlanFeature

    free_plan = Plan.objects.filter(code=PlanCodeType.FREE).first()
    limits = {}
    if free_plan:
        for pf in (
            PlanFeature.objects.filter(plan=free_plan)
            .select_related("feature")
            .iterator()
        ):
            code = pf.feature.code
            if pf.limit_value is not None:
                limits[code] = pf.limit_value + (1 if code == "space.max_count" else 0)

    cache.set(cache_key, limits, 3600)
    return limits


def _send_subscription_tasks(prefix, payload):
    for service in ("device", "space", "dashboard"):
        send_task(f"{service}_{prefix}", payload)


def downgrade_to_free(organization):
    """Downgrade an organization from any paid plan to the Free plan."""
    now = timezone.now()

    # 1. End all active non-Free subscriptions
    ended = (
        Subscription.objects.filter(
            organization=organization,
            period_end__gt=now,
        )
        .exclude(plan_item__plan__code=PlanCodeType.FREE)
        .update(period_end=now)
    )

    if not ended:
        logger.info(
            "No active paid subscription to downgrade for org %s — "
            "may already be on Free plan.",
            organization.slug_name,
        )

    # 2. Check if org already has an active Free subscription
    already_free = Subscription.objects.filter(
        organization=organization,
        period_end__gt=now,
        plan_item__plan__code=PlanCodeType.FREE,
    ).exists()
    if already_free:
        logger.info(
            "Org %s already has an active Free subscription, skipping creation.",
            organization.slug_name,
        )
    else:
        free_item = (
            PlanItem.objects.select_related("plan")
            .filter(
                plan__code=PlanCodeType.FREE,
                billing_cycle=BillingCycle.MONTHLY,
                is_active=True,
            )
            .first()
        )
        if free_item is None:
            logger.error(
                "Free plan item not found for org %s — cannot create Free subscription.",
                organization.slug_name,
            )
        else:
            duration_days = BILLING_CYCLE_DAYS.get(free_item.billing_cycle, 30)
            Subscription.objects.create(
                organization=organization,
                plan_item=free_item,
                period_start=now,
                period_end=now + timedelta(days=duration_days),
            )
            logger.info(
                "Created Free subscription for org %s (was on paid plan).",
                organization.slug_name,
            )

    # 3. Enqueue downgrade tasks to each service
    limits = _get_free_plan_limits()
    payload = {"org_slug": organization.slug_name, "limits": limits}

    _send_subscription_tasks("downgrade", payload)

    logger.info(
        "Org %s downgraded to Free — enqueued downgrade tasks.",
        organization.slug_name,
    )


def renew_subscription(organization):
    """Enqueue upgrade tasks so services re-activate deactivated resources."""
    payload = {"org_slug": organization.slug_name}

    _send_subscription_tasks("upgrade", payload)

    logger.info(
        "Org %s subscription renewed — enqueued upgrade tasks.",
        organization.slug_name,
    )
