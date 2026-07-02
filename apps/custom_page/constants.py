from django.db import models


class PageTypes(models.TextChoices):
    SIGN_IN = "sign_in"
    SIGN_UP = "sign_up"
    FORGET_PASSWORD = "forget_password"  # nosec B105
    CHANGE_PASSWORD = "change_password"  # nosec B105
