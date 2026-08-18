from django.db import migrations, models


def _next_month(value):
    if value.month == 12:
        return value.replace(year=value.year + 1, month=1)
    return value.replace(month=value.month + 1)


def backfill_scope_and_period(apps, schema_editor):
    FeatureUsage = apps.get_model("billing", "FeatureUsage")

    usages = FeatureUsage.objects.select_related("subscription").all()
    for usage in usages.iterator():
        usage.scope_type = "organization"
        usage.scope_id = usage.subscription.organization_id
        usage.period_start = usage.billing_period
        usage.period_end = _next_month(usage.billing_period)
        usage.save(
            update_fields=[
                "scope_type",
                "scope_id",
                "period_start",
                "period_end",
            ]
        )


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0002_seed_default_plans_and_features"),
    ]

    operations = [
        migrations.AddField(
            model_name="featureusage",
            name="scope_type",
            field=models.CharField(
                db_index=True, default="organization", max_length=32
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="featureusage",
            name="scope_id",
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="featureusage",
            name="period_start",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="featureusage",
            name="period_end",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_scope_and_period, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="featureusage",
            name="scope_id",
            field=models.UUIDField(db_index=True),
        ),
        migrations.AlterField(
            model_name="featureusage",
            name="period_start",
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name="featureusage",
            name="period_end",
            field=models.DateField(),
        ),
        migrations.RemoveField(
            model_name="featureusage",
            name="billing_period",
        ),
        migrations.AddConstraint(
            model_name="featureusage",
            constraint=models.UniqueConstraint(
                fields=(
                    "subscription",
                    "feature",
                    "scope_type",
                    "scope_id",
                    "period_start",
                    "period_end",
                ),
                name="unique_feature_usage_scope_period",
            ),
        ),
    ]
