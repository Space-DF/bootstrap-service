from apps.custom_page.constants import PageTypes
from apps.custom_page.models import CustomPage


def get_default_pages():
    return [
        {
            "page_type": PageTypes.SIGN_IN,
            "title": "Sign in to SpaceDF",
            "subtitle": "Sign in to manage your IoT devices",
            "metadata": {},
            "theme_colors": {},
            "background_image": "",
            "show_logo": True,
        },
        {
            "page_type": PageTypes.SIGN_UP,
            "title": "Sign up to SpaceDF",
            "subtitle": "Sign up to manage your IoT devices",
            "metadata": {},
            "theme_colors": {},
            "background_image": "",
            "show_logo": True,
        },
        {
            "page_type": PageTypes.FORGET_PASSWORD,
            "title": "Forgot Your Password?",
            "subtitle": "Enter your email address and we will send you instructions to reset your password.",
            "metadata": {},
            "theme_colors": {
                "background_color": "#FFFFFF",
            },
            "background_image": "",
            "show_logo": True,
        },
        {
            "page_type": PageTypes.CHANGE_PASSWORD,
            "title": "Create New Password",
            "subtitle": "Create your new password. If you forget it, then you have to do forget password",
            "metadata": {},
            "theme_colors": {
                "background_color": "#FFFFFF",
            },
            "background_image": "",
            "show_logo": True,
        },
    ]


def create_default_pages(organization):
    default_pages = get_default_pages()
    list_data = [
        CustomPage(
            organization=organization,
            page_type=page.get("page_type"),
            title=page.get("title"),
            subtitle=page.get("subtitle"),
            metadata=page.get("metadata"),
            theme_colors=page.get("theme_colors"),
            background_image=page.get("background_image"),
            show_logo=page.get("show_logo"),
        )
        for page in default_pages
    ]
    CustomPage.objects.bulk_create(list_data)
