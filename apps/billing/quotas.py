from common.apps.billing.constants import FeatureCode, FeatureUsageScope
from common.apps.billing.mixins import BaseQuota


class WhitelabelQuota(BaseQuota):
    reserve_actions = set()
    rules = {
        ("create", "update", "partial_update", "destroy"): {
            "feature": FeatureCode.WHITELABEL_ENABLED,
            "scope": FeatureUsageScope.ORGANIZATION,
        },
    }
