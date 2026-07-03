from django.db import migrations

from apps.custom_email.service import get_default_organization_emails


def backfill_organization_emails(apps, schema_editor):
    Organization = apps.get_model("organization", "Organization")
    OrganizationEmail = apps.get_model("custom_email", "OrganizationEmail")

    existing_pairs = set(
        OrganizationEmail.objects.values_list("organization_id", "email_type")
    )
    emails_to_create = []
    default_emails = get_default_organization_emails()

    for organization in Organization.objects.all().iterator():
        for email_data in default_emails:
            email_type = email_data["email_type"]
            if (organization.id, email_type) in existing_pairs:
                continue

            emails_to_create.append(
                OrganizationEmail(
                    organization_id=organization.id,
                    **email_data,
                )
            )

    if emails_to_create:
        OrganizationEmail.objects.bulk_create(emails_to_create, batch_size=100)


class Migration(migrations.Migration):
    dependencies = [
        ("custom_email", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            backfill_organization_emails,
            migrations.RunPython.noop,
        ),
    ]
