from django.db import models


class ThemeType(models.TextChoices):
    LIGHT = "light"
    DARK = "dark"
