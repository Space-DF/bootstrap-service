from rest_framework import serializers

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
