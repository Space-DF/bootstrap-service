import uuid
from django.db import migrations


def backfill_organization_settings(apps, schema_editor):
    from apps.organization_setting.services import (
        DEFAULT_DARK_THEME_VALUES,
        DEFAULT_LIGHT_THEME_VALUES,
        DEFAULT_ORGANIZATION_SETTING_VALUES,
    )

    Organization = apps.get_model("organization", "Organization")
    OrganizationSetting = apps.get_model("organization_setting", "OrganizationSetting")
    OrganizationTheme = apps.get_model("organization_setting", "OrganizationTheme")

    organizations = list(Organization.objects.values_list("id", flat=True))
    existing_setting_org_ids = set(
        OrganizationSetting.objects.values_list("organization_id", flat=True)
    )

    missing_settings = [
        OrganizationSetting(
            id=uuid.uuid4(),
            organization_id=organization_id,
            **DEFAULT_ORGANIZATION_SETTING_VALUES,
        )
        for organization_id in organizations
        if organization_id not in existing_setting_org_ids
    ]
    if missing_settings:
        OrganizationSetting.objects.bulk_create(missing_settings)

    settings = list(OrganizationSetting.objects.values("id", "organization_id"))
    existing_theme_keys = set(
        OrganizationTheme.objects.values_list("setting_id", "theme_key")
    )

    themes_to_create = []
    for setting in settings:
        for theme_key, theme_defaults in [
            ("light", DEFAULT_LIGHT_THEME_VALUES),
            ("dark", DEFAULT_DARK_THEME_VALUES),
        ]:
            theme_identity = (setting["id"], theme_key)
            if theme_identity in existing_theme_keys:
                continue

            themes_to_create.append(
                OrganizationTheme(
                    id=uuid.uuid4(),
                    setting_id=setting["id"],
                    theme_key=theme_key,
                    **theme_defaults,
                )
            )

    if themes_to_create:
        OrganizationTheme.objects.bulk_create(themes_to_create)


class Migration(migrations.Migration):
    dependencies = [
        ("organization_setting", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            backfill_organization_settings,
            migrations.RunPython.noop,
        ),
    ]
