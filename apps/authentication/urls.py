from django.urls import path

from apps.authentication.views import (
    ChangePasswordAPIView,
    ForgetPasswordView,
    LoginAPIView,
    ProfileAPIView,
    RefreshTokenView,
    SendEmailToConfirmView,
)

app_name = "auth"

urlpatterns = [
    path("auth/login", LoginAPIView.as_view(), name="login"),
    path(
        "auth/change-password", ChangePasswordAPIView.as_view(), name="change_password"
    ),
    path("auth/refresh-token", RefreshTokenView.as_view(), name="refresh_token"),
    path("auth/forget-password", ForgetPasswordView.as_view(), name="forget_password"),
    path("user/me", ProfileAPIView.as_view(), name="profile"),
    path(
        "auth/send-email-confirm",
        SendEmailToConfirmView.as_view(),
        name="send_email_confirm",
    ),
]
