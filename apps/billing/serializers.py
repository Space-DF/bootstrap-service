from rest_framework import serializers

from apps.billing.models import Feature, Plan, PlanFeature, PlanItem


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


class PlanItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanItem
        fields = [
            "id",
            "price",
            "icon",
            "currency",
            "discount",
            "billing_cycle",
            "is_active",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {"id": {"read_only": True}}


class PlanSerializer(serializers.ModelSerializer):
    plan_items = PlanItemSerializer(many=True, read_only=True)
    is_current_plan = serializers.BooleanField(read_only=True, default=True)

    class Meta:
        model = Plan
        fields = [
            "id",
            "name",
            "code",
            "description",
            "plan_items",
            "is_current_plan",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {"id": {"read_only": True}}


class PlanWithFeaturesSerializer(PlanSerializer):
    """Plan with nested feature definitions — for plan comparison views."""

    def to_representation(self, instance):
        data = super().to_representation(instance)
        plan_features = instance.plan_features.all()
        features = []
        support = []
        for plan_feature in plan_features:
            if plan_feature.feature.code.startswith("support."):
                support.append(plan_feature)
            else:
                features.append(plan_feature)

        data["features"] = PlanFeatureSerializer(features, many=True).data
        data["support"] = PlanFeatureSerializer(support, many=True).data
        return data

    class Meta(PlanSerializer.Meta):
        fields = list(PlanSerializer.Meta.fields) + ["plan_features"]


class ReserveQuotaSerializer(serializers.Serializer):
    organization = serializers.CharField()
    feature = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False,
    )
    amount = serializers.IntegerField(
        default=1,
        min_value=0,
        required=False,
    )


class ViewQuotaSerializer(serializers.Serializer):
    organization = serializers.CharField()
    feature = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False,
    )
