from common.apps.billing.constants import FeatureUsageScope
from rest_framework import serializers


class ReserveQuotaSerializer(serializers.Serializer):
    feature = serializers.CharField()
    scope_type = serializers.CharField(
        required=False,
        default=FeatureUsageScope.ORGANIZATION,
    )
    scope_id = serializers.UUIDField(required=False, allow_null=True)
    amount = serializers.IntegerField(
        default=1,
        min_value=0,
        required=False,
    )


class ViewQuotaSerializer(serializers.Serializer):
    feature = serializers.CharField()
    scope_type = serializers.CharField(
        required=False,
        default=FeatureUsageScope.ORGANIZATION,
    )
    scope_id = serializers.UUIDField(required=False, allow_null=True)
