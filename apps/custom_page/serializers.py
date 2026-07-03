from common.apps.upload_file.service import get_presigned_url
from django.conf import settings
from rest_framework import serializers

from apps.custom_page.models import CustomPage


class CustomPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomPage
        fields = [
            "id",
            "page_type",
            "title",
            "subtitle",
            "metadata",
            "theme_colors",
            "background_image",
            "show_logo",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
            "background_image": {"write_only": True},
            "created_at": {"read_only": True},
            "updated_at": {"read_only": True},
        }

    def validate_background_image(self, value):
        return value or ""

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.background_image:
            data["url_background_image"] = get_presigned_url(
                settings.AWS_S3.get("AWS_STORAGE_BUCKET_NAME"),
                f"uploads/{instance.background_image}",
            )
        return data
