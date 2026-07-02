from django.db import migrations

from apps.custom_page.service import get_default_pages


def backfill_default_custom_pages(apps, schema_editor):
    CustomPage = apps.get_model("custom_page", "CustomPage")
    Organization = apps.get_model("organization", "Organization")

    pages_to_create = []
    existing_pages = {}
    for org_id, page_type in CustomPage.objects.values_list(
        "organization_id", "page_type"
    ):
        if org_id not in existing_pages:
            existing_pages[org_id] = set()
        existing_pages[org_id].add(page_type)

    for organization in Organization.objects.all().iterator():
        existing_page_types = existing_pages.get(organization.id, set())

        for page in get_default_pages():
            if page["page_type"] in existing_page_types:
                continue

            pages_to_create.append(
                CustomPage(
                    organization_id=organization.id,
                    page_type=page["page_type"],
                    title=page["title"],
                    subtitle=page["subtitle"],
                    metadata=page["metadata"],
                    theme_colors=page["theme_colors"],
                    background_image=page["background_image"],
                    show_logo=page["show_logo"],
                )
            )

    if pages_to_create:
        CustomPage.objects.bulk_create(pages_to_create, batch_size=50)


class Migration(migrations.Migration):
    dependencies = [
        ("custom_page", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(backfill_default_custom_pages, migrations.RunPython.noop),
    ]
