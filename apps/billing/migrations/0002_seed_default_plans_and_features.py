"""Seed default Free and Pro plans with their feature definitions."""

from django.db import migrations

# Plan codes
FREE_PLAN_CODE = "free"
PRO_PLAN_CODE = "pro"

PLANS = [
    {
        "code": FREE_PLAN_CODE,
        "name": "Free",
        "description": "First 10 devices free.\n1 week Data Retention",
    },
    {
        "code": PRO_PLAN_CODE,
        "name": "Pro",
        "description": "Up to 100 devices\n6 months Data Retention",
    },
]

PLAN_ITEMS = [
    {
        "plan_code": FREE_PLAN_CODE,
        "price": 0,
        "currency": "USD",
        "discount": 0,
        "billing_cycle": "monthly",
    },
    {
        "plan_code": PRO_PLAN_CODE,
        "price": 99,
        "currency": "USD",
        "discount": 10,
        "billing_cycle": "monthly",
    },
]

# Feature catalog (9 features). value_type drives the PlanFeature shape:
#   limit    -> limit_value is the numeric cap (null = unlimited)
#   quota    -> limit_value is the quota amount
#   boolean  -> limit_value is null; use `enabled`
FEATURES = [
    {"code": "device.max_count", "name": "Device(s)", "value_type": "limit"},
    {"code": "space.max_count", "name": "Space(s)", "value_type": "limit"},
    {"code": "dashboard.max_count", "name": "Dashboard(s)", "value_type": "limit"},
    {
        "code": "dashboard.basic_widgets",
        "name": "Basic widgets",
        "value_type": "boolean",
    },
    {
        "code": "dashboard.custom_charts",
        "name": "Custom charts & maps",
        "value_type": "boolean",
    },
    {"code": "map_view.2d", "name": "2D map view", "value_type": "boolean"},
    {"code": "map_view.3d", "name": "3D map view", "value_type": "boolean"},
    {
        "code": "whitelabel.enabled",
        "name": "White-label branding",
        "value_type": "boolean",
    },
    {
        "code": "data_retention.days",
        "name": "Data retention (days)",
        "value_type": "quota",
    },
    {
        "code": "support.onboarding_video",
        "name": "Onboarding video",
        "value_type": "boolean",
    },
    {"code": "support.email", "name": "Email support", "value_type": "boolean"},
    {
        "code": "support.email_community",
        "name": "Email, community support",
        "value_type": "boolean",
    },
    {"code": "support.priority", "name": "Priority support", "value_type": "boolean"},
    {
        "code": "support.fully_maintenance",
        "name": "Fully maintenance",
        "value_type": "boolean",
    },
]

# Per-plan feature values. Keys are feature codes;
FREE_FEATURES = {
    "device.max_count": {"enabled": True, "limit_value": 10},
    "space.max_count": {"enabled": True, "limit_value": 1},
    "dashboard.max_count": {"enabled": True, "limit_value": 1},
    "dashboard.basic_widgets": {"enabled": True, "limit_value": None},
    "map_view.2d": {"enabled": True, "limit_value": None},
    "map_view.3d": {"enabled": True, "limit_value": None},
    "data_retention.days": {"enabled": True, "limit_value": 7},
    "support.onboarding_video": {"enabled": True, "limit_value": None},
    "support.email": {"enabled": True, "limit_value": None},
}

PRO_FEATURES = {
    "device.max_count": {"enabled": True, "limit_value": 100},
    "space.max_count": {"enabled": True, "limit_value": None},
    "dashboard.max_count": {"enabled": True, "limit_value": None},
    "dashboard.basic_widgets": {"enabled": True, "limit_value": None},
    "dashboard.custom_charts": {"enabled": True, "limit_value": None},
    "map_view.2d": {"enabled": True, "limit_value": None},
    "map_view.3d": {"enabled": True, "limit_value": None},
    "whitelabel.enabled": {"enabled": True, "limit_value": None},
    "data_retention.days": {"enabled": True, "limit_value": 180},
    "support.onboarding_video": {"enabled": True, "limit_value": None},
    "support.email": {"enabled": True, "limit_value": None},
    "support.email_community": {"enabled": True, "limit_value": None},
    "support.priority": {"enabled": True, "limit_value": None},
    "support.fully_maintenance": {"enabled": True, "limit_value": None},
}

PLAN_FEATURE_VALUES = {
    FREE_PLAN_CODE: FREE_FEATURES,
    PRO_PLAN_CODE: PRO_FEATURES,
}

FEATURE_CODES = [f["code"] for f in FEATURES]
PLAN_CODES = [p["code"] for p in PLANS]


def _upsert_plans(apps):
    Plan = apps.get_model("billing", "Plan")
    plans_by_code = {}
    for spec in PLANS:
        plan, _ = Plan.objects.update_or_create(
            code=spec["code"],
            defaults={
                "name": spec["name"],
                "description": spec["description"],
            },
        )
        plans_by_code[spec["code"]] = plan
    return plans_by_code


def _upsert_plan_items(apps, plans_by_code):
    PlanItem = apps.get_model("billing", "PlanItem")
    for spec in PLAN_ITEMS:
        PlanItem.objects.update_or_create(
            plan=plans_by_code[spec["plan_code"]],
            billing_cycle=spec["billing_cycle"],
            defaults={
                "price": spec["price"],
                "discount": spec["discount"],
                "currency": spec["currency"],
                "is_active": True,
            },
        )


def _upsert_features(apps):
    Feature = apps.get_model("billing", "Feature")
    features_by_code = {}
    for spec in FEATURES:
        feature, _ = Feature.objects.update_or_create(
            code=spec["code"],
            defaults={
                "name": spec["name"],
                "description": "",
                "value_type": spec["value_type"],
            },
        )
        features_by_code[spec["code"]] = feature
    return features_by_code


def _upsert_plan_features(apps, plans_by_code, features_by_code):
    PlanFeature = apps.get_model("billing", "PlanFeature")
    for plan_code, plan in plans_by_code.items():
        values = PLAN_FEATURE_VALUES.get(plan_code, {})
        for feature_code, feature in features_by_code.items():
            v = values.get(feature_code, {"enabled": False, "limit_value": None})
            PlanFeature.objects.update_or_create(
                plan=plan,
                feature=feature,
                defaults={
                    "enabled": v["enabled"],
                    "limit_value": v["limit_value"],
                },
            )


def forward(apps, schema_editor):
    plans_by_code = _upsert_plans(apps)
    _upsert_plan_items(apps, plans_by_code)
    features_by_code = _upsert_features(apps)
    _upsert_plan_features(apps, plans_by_code, features_by_code)


def reverse(apps, schema_editor):
    Plan = apps.get_model("billing", "Plan")
    PlanItem = apps.get_model("billing", "PlanItem")
    Subscription = apps.get_model("billing", "Subscription")
    if Subscription.objects.filter(plan_item__plan__code__in=PLAN_CODES).exists():
        raise RuntimeError(
            "Cannot reverse migration: active subscriptions exist for these plans."
        )
    PlanFeature = apps.get_model("billing", "PlanFeature")
    Feature = apps.get_model("billing", "Feature")
    # Delete seeded PlanFeatures, Plans, and Features by code.
    PlanFeature.objects.filter(
        plan__code__in=PLAN_CODES,
        feature__code__in=FEATURE_CODES,
    ).delete()
    for spec in PLAN_ITEMS:
        PlanItem.objects.filter(
            plan__code=spec["plan_code"],
            billing_cycle=spec["billing_cycle"],
        ).delete()
    Plan.objects.filter(code__in=PLAN_CODES).delete()
    Feature.objects.filter(code__in=FEATURE_CODES).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0001_initial"),
    ]

    operations = [migrations.RunPython(forward, reverse)]
