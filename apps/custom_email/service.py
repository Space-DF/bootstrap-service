from common.apps.upload_file.service import get_presigned_url
from django.conf import settings

from apps.custom_email.constants import EmailTypes
from apps.custom_email.models import OrganizationEmail
from apps.organization_setting.constants import ThemeType


def get_theme_logo_url(instance, theme_key):
    host = settings.HOST.rstrip("/")
    default_logo = "logo_white.png" if theme_key == ThemeType.DARK else "logo_black.png"
    organization = getattr(instance, "organization", None)
    if not organization:
        return f"{host}/static/images/branding/{default_logo}"

    setting = getattr(organization, "organization_settings", None)
    if not setting:
        return f"{host}/static/images/branding/{default_logo}"

    themes = getattr(setting, "_prefetched_objects_cache", {}).get("themes")
    if themes is not None:
        theme = next((item for item in themes if item.theme_key == theme_key), None)
    else:
        theme = setting.themes.filter(theme_key=theme_key).first()

    if not theme or not theme.logo:
        return f"{host}/static/images/branding/{default_logo}"

    return get_presigned_url(
        settings.AWS_S3.get("AWS_STORAGE_BUCKET_NAME"),
        f"uploads/{theme.logo}",
    )


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


def get_custom_email_item(email_type):
    from apps.custom_email.serializers import OrganizationEmailSerializer

    custom_email = next(
        (
            item
            for item in get_default_organization_emails()
            if item.get("email_type") == email_type
        ),
        None,
    )
    if not custom_email:
        return {}

    return OrganizationEmailSerializer(OrganizationEmail(**custom_email)).data
