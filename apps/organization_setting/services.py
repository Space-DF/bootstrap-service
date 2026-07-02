from apps.organization.models import Organization
from apps.organization_setting.constants import ThemeType
from apps.organization_setting.models import OrganizationSetting, OrganizationTheme

DEFAULT_ORGANIZATION_SETTING_VALUES = {
    "brand_name": "SpaceDF",
    "site_title": "SpaceDF - No-Code IoT Management Platform",
    "site_description": (
        "SpaceDF is a ready-to-use IoT platform that lets you connect, "
        "manage, and control all your devices from a single dashboard "
        "with no-code and minimal setup."
    ),
    "border_radius": {
        "button": 8,
        "input": 8,
        "card": 6,
    },
}

DEFAULT_DARK_THEME_VALUES = {
    "favicon": "",
    "logo": "",
    "theme_colors": {
        "primary": "#4006AA",
        "outline": "#171A28",
        "background": "#171A28",
        "text": "#FFFFFF",
        "input": "#090C18",
        "support_text": "#6A749C",
        "device_card": "#202431",
        "widget_card": "#202431",
        "widget_border": "#242A46",
    },
}

DEFAULT_LIGHT_THEME_VALUES = {
    "favicon": "",
    "logo": "",
    "theme_colors": {
        "primary": "#171A28",
        "outline": "#FFFFFF",
        "background": "#FFFFFF",
        "text": "#1F2937",
        "input": "#F0F1F3",
        "support_text": "#667085",
        "device_card": "#F0F1F3",
        "widget_card": "#FFFFFF",
        "widget_border": "#F0F1F3",
    },
}


def create_default_organization_setting(organization: Organization):
    setting = OrganizationSetting.objects.create(
        organization=organization,
        **DEFAULT_ORGANIZATION_SETTING_VALUES,
    )
    OrganizationTheme.objects.bulk_create(
        [
            OrganizationTheme(
                setting=setting,
                theme_key=ThemeType.LIGHT,
                **DEFAULT_LIGHT_THEME_VALUES,
            ),
            OrganizationTheme(
                setting=setting,
                theme_key=ThemeType.DARK,
                **DEFAULT_DARK_THEME_VALUES,
            ),
        ]
    )
