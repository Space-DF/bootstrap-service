from common.apps.upload_file.service import get_presigned_url
from django.conf import settings
from django.db import transaction
from rest_framework import serializers

from apps.custom_page.serializers import CustomPageSerializer
from apps.organization_setting.models import OrganizationSetting, OrganizationTheme


class OrganizationThemeSerializer(serializers.ModelSerializer):
    url_logo = serializers.SerializerMethodField()
    url_favicon = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationTheme
        fields = [
            "id",
            "theme_key",
            "favicon",
            "logo",
            "theme_colors",
            "url_logo",
            "url_favicon",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
            "favicon": {"write_only": True},
            "logo": {"write_only": True},
            "url_logo": {"read_only": True},
            "url_favicon": {"read_only": True},
        }

    def get_url_logo(self, instance):
        host = settings.HOST.rstrip("/")
        if not instance.logo:
            default_logo = (
                "logo_white.png" if instance.theme_key == "dark" else "logo_black.png"
            )
            return f"{host}/static/images/branding/{default_logo}"
        return get_presigned_url(
            settings.AWS_S3.get("AWS_STORAGE_BUCKET_NAME"),
            f"uploads/{instance.logo}",
        )

    def get_url_favicon(self, instance):
        host = settings.HOST.rstrip("/")
        if not instance.favicon:
            default_favicon = (
                "favicon_white.png"
                if instance.theme_key == "dark"
                else "favicon_black.png"
            )
            return f"{host}/static/images/branding/{default_favicon}"
        return get_presigned_url(
            settings.AWS_S3.get("AWS_STORAGE_BUCKET_NAME"),
            f"uploads/{instance.favicon}",
        )


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
        read_only_fields = ["id"]


class UpdateOrganizationSettingSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    site_title = serializers.CharField(required=False, allow_blank=True)
    site_description = serializers.CharField(required=False, allow_blank=True)
    border_radius = serializers.JSONField(required=False)
    themes = OrganizationThemeSerializer(many=True, required=False)
    custom_pages = CustomPageSerializer(many=True, required=False)
    brand_name = serializers.CharField(required=False, allow_blank=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def _save_instance(self, instance, data):
        for attr, value in data.items():
            setattr(instance, attr, value)
        instance.save()

    def _get_instance(self, queryset, data, fallback_field, default=None):
        data = data.copy()
        object_id = data.pop("id", None)
        fallback_value = data.get(fallback_field)
        instance = queryset.filter(id=object_id).first() if object_id else None
        if instance is None and fallback_value:
            instance = queryset.filter(**{fallback_field: fallback_value}).first()
        return instance or default(data)

    def _update_themes(self, instance, themes_data):
        for theme_data in themes_data or []:
            theme = self._get_instance(
                instance.themes,
                theme_data,
                "theme_key",
                lambda data: instance.themes.create(
                    theme_key=data.get("theme_key") or "light"
                ),
            )
            self._save_instance(theme, theme_data)

    def to_representation(self, instance):
        data = OrganizationSettingSerializer(instance, context=self.context).data
        data["custom_pages"] = CustomPageSerializer(
            instance.organization.organization_custom_page.all(),
            many=True,
            context=self.context,
        ).data
        return data

    def update(self, instance, validated_data):
        with transaction.atomic():
            custom_pages_data = validated_data.pop("custom_pages", [])
            themes_data = validated_data.pop("themes", [])

            self._save_instance(instance, validated_data)
            self._update_themes(instance, themes_data)

            pages = instance.organization.organization_custom_page
            for page_data in custom_pages_data:
                page = self._get_instance(pages, page_data, "page_type")
                if page is None:
                    continue
                self._save_instance(page, page_data)

        return instance
