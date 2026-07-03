from common.apps.upload_file.service import get_presigned_url
from django.conf import settings
from rest_framework import serializers

from apps.custom_email.constants import EmailTypes
from apps.custom_email.models import OrganizationEmail
from apps.custom_email.service import get_theme_logo_url


class OrganizationEmailSerializer(serializers.ModelSerializer):
    brand_logo_dark = serializers.SerializerMethodField()
    brand_logo_light = serializers.SerializerMethodField()
    brand_name = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationEmail
        fields = [
            "id",
            "brand_logo_dark",
            "brand_logo_light",
            "brand_name",
            "email_type",
            "email_type",
            "sender_name",
            "sender_email",
            "theme_colors",
            "footer_text",
            "header_image",
            "show_logo",
            "social_links",
            "metadata",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
            "email_type": {"required": True},
            "header_image": {"write_only": True},
            "brand_logo_dark": {"read_only": True},
            "brand_logo_light": {"read_only": True},
            "brand_name": {"read_only": True},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.header_image:
            data["url_header_image"] = get_presigned_url(
                settings.AWS_S3.get("AWS_STORAGE_BUCKET_NAME"),
                f"uploads/{instance.header_image}",
            )
            return data

        image_mapping = {
            EmailTypes.INVITATION_TO_SPACE: "auth/invitation.png",
            EmailTypes.VERIFICATION_CODE: "auth/verification_code.png",
            EmailTypes.RESET_PASSWORD: "auth/forget_password.png",
        }
        image_path = image_mapping.get(instance.email_type, "")
        host = settings.HOST.rstrip("/")
        data["url_header_image"] = (
            f"{host}/static/images/{image_path}" if image_path else ""
        )
        return data

    def get_brand_logo_dark(self, instance):
        return get_theme_logo_url(instance, "dark")

    def get_brand_logo_light(self, instance):
        return get_theme_logo_url(instance, "light")

    def get_brand_name(self, instance):
        organization = getattr(instance, "organization", None)
        setting = (
            getattr(organization, "organization_settings", None)
            if organization
            else None
        )
        return getattr(setting, "brand_name", "") or ""
