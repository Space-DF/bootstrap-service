import logging
from datetime import timedelta

from common.apps.billing.constants import FeatureUsageScope
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


def get_free_plan_item():
    return (
        PlanItem.objects.select_related("plan")
        .filter(
            plan__code=PlanCodeType.FREE,
            billing_cycle=BillingCycle.MONTHLY,
            is_active=True,
        )
        .first()
    )


def get_current_subscription(organization, for_update=False):
    queryset = Subscription.objects.filter(organization=organization)
    if for_update:
        queryset = queryset.select_for_update()
    else:
        queryset = queryset.select_related("plan_item__plan")

    now = timezone.now()
    subscription = (
        queryset.filter(period_end__gt=now)
        .order_by("-period_end", "-updated_at", "-created_at")
        .first()
    )
    if subscription:
        return subscription

    return queryset.order_by("-created_at").first()


def create_default_subscription(organization, owner=None):
    """Create the default Free subscription for a newly-created organization.

    Idempotent-safe: returns None (without raising) if the Free plan has not
    been seeded yet, so organization creation never fails because of billing
    setup.

    Args:
        organization: The newly-created Organization.
    """
    existing_subscription = get_current_subscription(organization)
    if existing_subscription is not None:
        logger.info(
            "Subscription already exists for org %s, skipping default subscription "
            "creation.",
            organization.slug_name,
        )
        return existing_subscription

    plan_item = get_free_plan_item()
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
    subscription = get_current_subscription(organization)
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


def _current_period():
    period_start = timezone.now().date().replace(day=1)
    if period_start.month == 12:
        period_end = period_start.replace(
            year=period_start.year + 1,
            month=1,
        )
    else:
        period_end = period_start.replace(month=period_start.month + 1)
    return period_start, period_end


def _resolve_scope(organization, scope_type=None, scope_id=None):
    scope_type = scope_type or FeatureUsageScope.ORGANIZATION
    if scope_type == FeatureUsageScope.ORGANIZATION:
        return scope_type, organization.id
    if scope_id is None:
        raise ValueError(f"scope_id is required for scope_type '{scope_type}'.")
    return scope_type, scope_id


def _usage_lookup(
    subscription_id,
    feature_id,
    period_start,
    period_end,
    scope_type,
    scope_id,
):
    return {
        "subscription_id": subscription_id,
        "feature_id": feature_id,
        "scope_type": scope_type,
        "scope_id": scope_id,
        "period_start": period_start,
        "period_end": period_end,
    }


def reserve_quota(
    organization,
    feature_code,
    amount=1,
    scope_type=None,
    scope_id=None,
):
    """Atomically reserve ``amount`` of a feature for the org's current period.
    Returns ``(reserved: bool, error: str | None)``. Limited features increment
    ``FeatureUsage.used_value`` atomically for the resolved scope.
    Unlimited features are allowed without tracking usage.
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
            period_start, period_end = _current_period()
            scope_type, scope_id = _resolve_scope(organization, scope_type, scope_id)
            usage, _ = FeatureUsage.objects.select_for_update().get_or_create(
                **_usage_lookup(
                    subscription_id,
                    feature_id,
                    period_start,
                    period_end,
                    scope_type,
                    scope_id,
                ),
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


def reserve_quotas(
    organization,
    feature_codes,
    amount=1,
    scope_type=None,
    scope_id=None,
):
    reserved_features = []

    for feature_code in feature_codes:
        reserved, error = reserve_quota(
            organization,
            feature_code,
            amount,
            scope_type,
            scope_id,
        )
        if not reserved:
            for reserved_feature in reserved_features:
                release_quota(
                    organization,
                    reserved_feature,
                    amount,
                    scope_type,
                    scope_id,
                )
            return False, error

        if amount > 0:
            reserved_features.append(feature_code)

    return True, None


def release_quota(
    organization,
    feature_code,
    amount=1,
    scope_type=None,
    scope_id=None,
):
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
            period_start, period_end = _current_period()
            scope_type, scope_id = _resolve_scope(organization, scope_type, scope_id)
            usage = (
                FeatureUsage.objects.select_for_update()
                .filter(
                    **_usage_lookup(
                        subscription_id,
                        feature_id,
                        period_start,
                        period_end,
                        scope_type,
                        scope_id,
                    )
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


def release_quotas(
    organization,
    feature_codes,
    amount=1,
    scope_type=None,
    scope_id=None,
):
    for feature_code in feature_codes:
        release_quota(organization, feature_code, amount, scope_type, scope_id)


def get_quota(organization, feature_code, scope_type=None, scope_id=None):
    """Get quota for a feature."""
    slug = organization.slug_name
    try:
        subscription_id, feature_id, _, is_allowed = _get_quota_meta(
            organization, feature_code
        )
        if subscription_id is None or feature_id is None or not is_allowed:
            return 0

        period_start, period_end = _current_period()
        scope_type, scope_id = _resolve_scope(organization, scope_type, scope_id)
        usage = FeatureUsage.objects.filter(
            **_usage_lookup(
                subscription_id,
                feature_id,
                period_start,
                period_end,
                scope_type,
                scope_id,
            )
        ).first()
        if usage is None:
            return 0
        return usage.used_value
    except Exception as e:  # noqa: BLE001
        logger.error("get_quota failed for %s/%s: %s", slug, feature_code, e)
        return 0


def get_quotas(organization, feature_codes, scope_type=None, scope_id=None):
    return {
        feature_code: get_quota(organization, feature_code, scope_type, scope_id)
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
                limits[code] = pf.limit_value

    cache.set(cache_key, limits, 3600)
    return limits


def _send_subscription_tasks(prefix, payload):
    for service in ("device", "space", "dashboard"):
        send_task(f"{service}_{prefix}", payload)


def downgrade_to_free(organization):
    """Downgrade an organization from any paid plan to the Free plan."""
    now = timezone.now()

    free_item = get_free_plan_item()
    if free_item is None:
        logger.error(
            "Free plan item not found for org %s — cannot downgrade subscription.",
            organization.slug_name,
        )
        return

    with transaction.atomic():
        subscription = get_current_subscription(organization, for_update=True)
        if subscription is None:
            logger.warning(
                "No subscription found for org %s — cannot downgrade to Free.",
                organization.slug_name,
            )
            return

        Subscription.objects.filter(
            organization=organization,
            period_end__gt=now,
        ).exclude(id=subscription.id).update(period_end=now)

        duration_days = BILLING_CYCLE_DAYS.get(free_item.billing_cycle, 30)
        subscription.plan_item = free_item
        subscription.period_start = now
        subscription.period_end = now + timedelta(days=duration_days)
        subscription.save(
            update_fields=["plan_item", "period_start", "period_end", "updated_at"]
        )

        logger.info(
            "Updated existing subscription %s for org %s to Free.",
            subscription.id,
            organization.slug_name,
        )

    limits = _get_free_plan_limits()
    payload = {"org_slug": organization.slug_name, "limits": limits}

    _send_subscription_tasks("downgrade", payload)

    logger.info(
        "Org %s downgraded to Free — enqueued downgrade tasks.",
        organization.slug_name,
    )


def _update_subscription_to_free(subscription):
    """Update a specific subscription row to Free."""
    organization = subscription.organization
    free_item = get_free_plan_item()
    if free_item is None:
        logger.error(
            "Free plan item not found for org %s — cannot downgrade subscription %s.",
            organization.slug_name,
            subscription.id,
        )
        return False

    now = timezone.now()
    duration_days = BILLING_CYCLE_DAYS.get(free_item.billing_cycle, 30)
    with transaction.atomic():
        Subscription.objects.filter(
            organization=organization,
            period_end__gt=now,
        ).exclude(id=subscription.id).update(period_end=now)

        subscription.plan_item = free_item
        subscription.period_start = now
        subscription.period_end = now + timedelta(days=duration_days)
        subscription.save(
            update_fields=["plan_item", "period_start", "period_end", "updated_at"]
        )
    return True


def downgrade_subscription_to_free(subscription):
    """Downgrade a specific subscription row to Free and enforce Free limits."""
    updated = _update_subscription_to_free(subscription)
    if not updated:
        return False

    limits = _get_free_plan_limits()
    payload = {"org_slug": subscription.organization.slug_name, "limits": limits}
    _send_subscription_tasks("downgrade", payload)

    logger.info(
        "Subscription %s for org %s downgraded to Free — enqueued downgrade tasks.",
        subscription.id,
        subscription.organization.slug_name,
    )
    return True


def renew_subscription(organization):
    """Enqueue upgrade tasks so services re-activate deactivated resources."""
    payload = {"org_slug": organization.slug_name}

    _send_subscription_tasks("upgrade", payload)

    logger.info(
        "Org %s subscription renewed — enqueued upgrade tasks.",
        organization.slug_name,
    )
