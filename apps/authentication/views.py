from datetime import datetime, timezone

from common.apps.refresh_tokens.serializers import TokenPairSerializer
from common.utils.send_email import send_email
from common.utils.token_jwt import generate_token
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.authentication.models import RootUser
from apps.authentication.serializers import (
    ChangePasswordSerializer,
    ForgetPasswordSerializer,
    SendEmailSerializer,
    UserSerializer,
)
from apps.authentication.services import (
    create_organization_access_token,
    render_email_format,
)


class LoginAPIView(TokenObtainPairView):
    authentication_classes = []

    @swagger_auto_schema(
        responses={status.HTTP_201_CREATED: TokenPairSerializer},
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        return super().post(request, *args, **kwargs)


class RefreshTokenView(TokenRefreshView):
    authentication_classes = []
    _serializer_class = "apps.authentication.serializers.CustomTokenRefreshSerializer"

    def get_serializer_context(self):
        context = super().get_serializer_context()
        return {
            **context,
            "access_token_handler": create_organization_access_token,
            "access_token_handler_params": {},
        }


class SendEmailToConfirmView(generics.GenericAPIView):
    serializer_class = SendEmailSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        if not RootUser.objects.filter(email=email).exists():
            return Response(
                {"result": "No account found with this email address."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subject = "🔒 Forgot your password? Reset now"
        token = generate_token({"email": email})
        data = {
            "redirect_url": f"{settings.HOST_FRONTEND_ADMIN}/auth/reset-password?token={token}",
            "host": settings.HOST,
        }
        message = render_email_format("email_forget_password.html", data)
        send_email(settings.DEFAULT_FROM_EMAIL, [email], subject, message)
        return Response(
            {
                "result": "Please check your email to continue the password reset process"
            },
            status=status.HTTP_200_OK,
        )


class ForgetPasswordView(generics.GenericAPIView):
    serializer_class = ForgetPasswordSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_str = serializer.validated_data["token"]
        if cache.get(f"used_token: {token_str}"):
            return Response(
                {"error": "This token has already been used"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = AccessToken(token_str)
            root_user = RootUser.objects.filter(email=token.get("email")).first()
            if root_user:
                root_user.set_password(serializer.validated_data["password"])
                root_user.save()

                exp_timestamp = token.get("exp")
                exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                ttl_seconds = int((exp_datetime - token.current_time).total_seconds())
                cache.set(f"used_token: {token_str}", True, timeout=ttl_seconds)

                return Response(
                    {"result": "The password changed successfully"},
                    status=status.HTTP_200_OK,
                )

            return Response(
                {"result": "The account for this email does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": f"Invalid or expired token.{e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ChangePasswordAPIView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer

    def get_object(self):
        user_id = self.request.headers.get("X-User-ID", None)
        if not user_id:
            return None
        return get_object_or_404(RootUser, id=user_id)

    def put(self, request: Request):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response("helloworld", status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    queryset = RootUser.objects.all()

    def get_object(self):
        user_id = self.request.headers.get("X-User-ID", None)
        if user_id is None:
            raise NotFound("The user not found")
        return get_object_or_404(RootUser, id=user_id)
