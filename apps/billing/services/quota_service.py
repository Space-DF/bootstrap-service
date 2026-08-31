from apps.billing.services.subscription import release_quota, reserve_quota
from apps.organization.models import Organization


class BillingQuotaService:
    allow_missing_organization = False

    def _get_organization(self, organization_slug):
        return Organization.objects.filter(slug_name=organization_slug).first()

    def reserve_quota(
        self,
        organization_slug,
        feature,
        amount=1,
        scope_type=None,
        scope_id=None,
    ):
        organization = self._get_organization(organization_slug)
        if organization is None:
            return False, "Organization context required."

        return reserve_quota(
            organization,
            feature,
            amount,
            scope_type=scope_type,
            scope_id=scope_id,
        )

    def release_quota(
        self,
        organization_slug,
        feature,
        amount=1,
        scope_type=None,
        scope_id=None,
    ):
        organization = self._get_organization(organization_slug)
        if organization is None:
            return None

        return release_quota(
            organization,
            feature,
            amount,
            scope_type=scope_type,
            scope_id=scope_id,
        )


billing_quota_service = BillingQuotaService()
