from common.apps.upload_file.service import get_presigned_url
from common.celery import constants
from common.celery.task_senders import send_task
from django.conf import settings
from rest_framework import serializers

from apps.billing.constants import PlanCodeType
from apps.billing.services.subscription import get_current_subscription
from apps.organization.models import Organization


class OrganizationSerializer(serializers.ModelSerializer):
    created_by = serializers.UUIDField(read_only=True)
    total_member = serializers.IntegerField(read_only=True)

    class Meta:
        model = Organization
        fields = "__all__"
        extra_kwargs = {
            "id": {"read_only": True},
            "is_active": {"read_only": True},
            "created_at": {"read_only": True},
            "updated_at": {"read_only": True},
        }

    def validate_slug_name(self, data):
        if "_" in data:
            raise serializers.ValidationError(detail="slug name is invalid")
        return data

    def update(self, instance, validated_data):
        old_logo = instance.logo
        new_logo = validated_data.get("logo", old_logo)
        instance = super().update(instance, validated_data)
        if old_logo and old_logo != new_logo:
            send_task(
                name=constants.CONSOLE_SERVICE_DELETE_UPLOAD_FILE,
                message={
                    "bucket_name": settings.AWS_S3.get("AWS_STORAGE_BUCKET_NAME"),
                    "link_file": f"uploads/{old_logo}",
                },
            )
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        subscription = get_current_subscription(instance)
        if subscription and subscription.plan_item and subscription.plan_item.plan:
            data["plan"] = subscription.plan_item.plan.code
            data["period_start"] = subscription.period_start
            data["period_end"] = subscription.period_end
        else:
            data["plan"] = PlanCodeType.FREE
            data["period_start"] = None
            data["period_end"] = None

        if instance.logo and instance.logo not in ["", None]:
            data["url_logo"] = get_presigned_url(
                settings.AWS_S3.get("AWS_STORAGE_BUCKET_NAME"),
                f"uploads/{instance.logo}",
            )
        return data
