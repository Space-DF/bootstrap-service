from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.models import RootUser
from apps.billing.models import Subscription
from apps.contact_sales.service import (
    get_contact_sales_lead,
    process_contact_sales_lead,
)
from apps.organization.models import Organization


class ContactSalesView(APIView):
    """Forward a contact-sales request from a logged-in org user.
    All lead details are derived from the session — the caller supplies nothing.
    """

    authentication_classes = []

    def post(self, request):
        user_id = request.headers.get("X-User-ID")
        user = get_object_or_404(
            RootUser.objects.only(
                "id", "email", "first_name", "last_name", "company_name"
            ),
            id=user_id,
        )

        org_slug = request.headers.get("X-Organization")
        if org_slug is None:
            return Response(
                {"error": "Organization slug is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        org = (
            Organization.objects.filter(slug_name=org_slug)
            .only("name", "slug_name")
            .first()
        )
        if org is None:
            return Response(
                {"error": f"Organization {org_slug} not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        process_contact_sales_lead(user, org)

        return Response(
            {"message": "Your request has been sent to our sales team."},
            status=status.HTTP_200_OK,
        )


class ContactSalesStatusView(APIView):
    """Return the latest contact-sales lead for the caller's org."""

    authentication_classes = []

    def get(self, request):
        org_slug = request.headers.get("X-Organization")
        if not org_slug:
            return Response(
                {"error": "Organization slug is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subscription = Subscription.objects.filter(
            organization__slug_name=org_slug,
            period_end__gt=timezone.now(),
        ).first()

        if subscription is None:
            return Response(
                {
                    "error": "No active subscription found for this organization.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        lead = get_contact_sales_lead(str(subscription.id))

        return Response(
            {"result": lead is not None},
            status=status.HTTP_200_OK,
        )
