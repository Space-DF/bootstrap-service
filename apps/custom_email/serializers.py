from common.apps.upload_file.service import get_presigned_url
from django.conf import settings
from rest_framework import serializers

from apps.custom_email.constants import EmailTypes
from apps.custom_email.models import OrganizationEmail


class OrganizationEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationEmail
        fields = [
            "id",
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
