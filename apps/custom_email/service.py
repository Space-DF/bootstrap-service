from apps.custom_email.constants import EmailTypes
from apps.custom_email.models import OrganizationEmail


def get_default_organization_emails():
    common_data = {
        "sender_name": "The @SpaceDF team",
        "sender_email": "support@spacedf.com",
        "footer_text": "©2025 Digital Fortress. All rights reserved.",
        "header_image": "",
        "show_logo": True,
        "social_links": {
            "linkedin_url": "https://vn.linkedin.com/company/digital-fortress-vn",
            "facebook_url": "https://www.facebook.com/digitalfortress.dev/",
            "tiktok_url": "",
            "instagram_url": "https://www.instagram.com/df.iot/",
        },
        "metadata": {
            "show_facebook": True,
            "show_instagram": True,
            "show_linkedin": True,
            "show_tiktok": False,
        },
    }
    return [
        {
            **common_data,
            "email_type": EmailTypes.INVITATION_TO_SPACE,
            "theme_colors": {
                "background_color": "#FFFFFF",
                "primary_color": "#171A28",
            },
        },
        {
            **common_data,
            "email_type": EmailTypes.VERIFICATION_CODE,
            "theme_colors": {
                "background_color": "#FFFFFF",
                "primary_color": "#171A28",
            },
        },
        {
            **common_data,
            "email_type": EmailTypes.RESET_PASSWORD,
            "theme_colors": {
                "background_color": "#FFFFFF",
                "primary_color": "#171A28",
            },
        },
    ]


def create_default_organization_email(organization):
    return OrganizationEmail.objects.bulk_create(
        [
            OrganizationEmail(organization=organization, **email_data)
            for email_data in get_default_organization_emails()
        ]
    )
