from rest_framework import serializers

from apps.billing.models import Feature, Plan, PlanFeature


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = [
            "id",
            "code",
            "name",
            "description",
            "value_type",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
        }


class PlanFeatureSerializer(serializers.ModelSerializer):
    feature = FeatureSerializer(read_only=True)

    class Meta:
        model = PlanFeature
        fields = [
            "id",
            "feature",
            "enabled",
            "limit_value",
            "metadata",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
        }


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = "__all__"
        extra_kwargs = {"id": {"read_only": True}}
