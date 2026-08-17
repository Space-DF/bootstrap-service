from common.utils.email_context import get_email_context, render_email_format
from common.utils.send_email import send_email
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from apps.billing.constants import PlanCodeType
from apps.billing.services.subscription import get_current_subscription
from apps.contact_sales.constants import LEAD_CACHE_PREFIX, LEAD_CACHE_TTL


def process_contact_sales_lead(user, org):
    """Build lead from user + org, send email, store in Redis."""
    subscription = get_current_subscription(org)

    if subscription and get_contact_sales_lead(str(subscription.id)):
        return

    envelope = {
        "header_image_url": f"{settings.HOST}/static/images/auth/subscription_request.png",
        "plan_name": PlanCodeType.PRO.upper(),
        "subscription_id": str(subscription.id) if subscription else None,
        "name": _user_display_name(user),
        "email": user.email,
        "company_name": user.company_name,
        "org_name": org.name,
        "org_slug": org.slug_name,
        "user_id": str(user.id),
        "submitted_at": timezone.now().isoformat(),
    }

    # Email first — if SES fails, exception propagates, lead never stored
    _send_contact_sales_email(envelope)
    _store_contact_sales_lead(envelope)


def _user_display_name(user):
    full = f"{user.first_name or ''} {user.last_name or ''}".strip()
    return full or user.email


def _store_contact_sales_lead(envelope):
    subscription_id = envelope.get("subscription_id")
    if not subscription_id:
        return

    cache.set(
        "{}:{}".format(LEAD_CACHE_PREFIX, subscription_id),
        envelope,
        timeout=LEAD_CACHE_TTL,
    )


def get_contact_sales_lead(subscription_id):
    """Return the latest contact-sales lead for an org."""
    return cache.get("{}:{}".format(LEAD_CACHE_PREFIX, subscription_id))


def _send_contact_sales_email(envelope):
    email_context = get_email_context(
        {
            "host": settings.HOST,
            **envelope,
        },
        custom_email={},
    )
    message = render_email_format("email_contact_sales.html", email_context)
    subject = f"New Subscription Request - {envelope.get('plan_name', 'N/A')}"
    send_email(
        settings.DEFAULT_FROM_EMAIL,
        [settings.SALES_CONTACT_EMAIL],
        subject,
        message,
    )
