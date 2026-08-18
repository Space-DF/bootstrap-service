from common.apps.upload_file.service import get_presigned_url
from django.conf import settings
from django.db import transaction
from rest_framework import serializers

from apps.custom_email.serializers import OrganizationEmailSerializer
from apps.custom_page.serializers import CustomPageSerializer
from apps.organization_setting.models import OrganizationSetting, OrganizationTheme


class OrganizationThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationTheme
        fields = [
            "id",
            "theme_key",
            "favicon",
            "logo",
            "theme_colors",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
            "favicon": {"write_only": True},
            "logo": {"write_only": True},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        aws_s3 = getattr(settings, "AWS_S3", None)
        bucket_name = aws_s3.get("AWS_STORAGE_BUCKET_NAME") if aws_s3 else None
        data["url_logo"] = (
            get_presigned_url(bucket_name, f"uploads/{instance.logo}")
            if instance.logo and bucket_name
            else None
        )
        data["url_favicon"] = (
            get_presigned_url(bucket_name, f"uploads/{instance.favicon}")
            if instance.favicon and bucket_name
            else None
        )
        return data


class OrganizationSettingSerializer(serializers.ModelSerializer):
    themes = OrganizationThemeSerializer(many=True, required=False)

    class Meta:
        model = OrganizationSetting
        fields = [
            "id",
            "site_title",
            "site_description",
            "border_radius",
            "themes",
            "brand_name",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
        }


class OrganizationSettingWithPagesSerializer(OrganizationSettingSerializer):
    custom_pages = CustomPageSerializer(
        many=True,
        read_only=True,
        source="organization_setting_custom_page",
    )

    class Meta(OrganizationSettingSerializer.Meta):
        fields = OrganizationSettingSerializer.Meta.fields + [
            "custom_pages",
        ]


class UpdateOrganizationSettingSerializer(OrganizationSettingSerializer):
    custom_pages = CustomPageSerializer(
        many=True,
        required=False,
        source="organization_setting_custom_page",
    )
    custom_emails = OrganizationEmailSerializer(
        many=True,
        required=False,
        source="organization_setting_custom_emails",
    )

    class Meta(OrganizationSettingSerializer.Meta):
        fields = OrganizationSettingSerializer.Meta.fields + [
            "custom_pages",
            "custom_emails",
        ]

    def _update_instance(self, instance, data):
        for field, value in data.items():
            setattr(instance, field, value)
        instance.save()

    def _upsert(
        self,
        manager,
        items,
        *,
        lookup_field,
        create_kwargs=None,
        create_if_missing=True,
    ):
        if not items:
            return

        create_kwargs = create_kwargs or {}
        for data in items:
            data = data.copy()
            object_id = data.pop("id", None)
            lookup_value = data.get(lookup_field)
            object = None

            if object_id:
                object = manager.filter(id=object_id).first()

            if object is None and lookup_value is not None:
                object = manager.filter(**{lookup_field: lookup_value}).first()

            if object is None:
                if not create_if_missing:
                    continue

                create_data = dict(create_kwargs)
                if lookup_field is not None and lookup_value is not None:
                    create_data[lookup_field] = lookup_value

                object = manager.create(**create_data)
            self._update_instance(object, data)

    @transaction.atomic
    def update(self, instance, validated_data):
        themes = validated_data.pop("themes", [])
        custom_pages = validated_data.pop("organization_setting_custom_page", [])
        custom_emails = validated_data.pop("organization_setting_custom_emails", [])

        self._update_instance(instance, validated_data)

        self._upsert(
            manager=instance.themes,
            items=themes,
            lookup_field="theme_key",
            create_kwargs={"theme_key": "light"},
        )

        self._upsert(
            manager=instance.organization_setting_custom_emails,
            items=custom_emails,
            lookup_field="email_type",
        )

        self._upsert(
            manager=instance.organization_setting_custom_page,
            items=custom_pages,
            lookup_field="page_type",
        )

        return instance
