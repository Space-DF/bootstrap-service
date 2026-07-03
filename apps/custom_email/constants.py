from django.db import models


class EmailTypes(models.TextChoices):
    INVITATION_TO_SPACE = "invitation_to_space"
    VERIFICATION_CODE = "verification_code"
    RESET_PASSWORD = "reset_password"  # nosec B105
