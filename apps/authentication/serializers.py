from common.apps.refresh_tokens.serializers import (
    BaseTokenObtainPairSerializer,
    CustomTokenRefreshSerializer,
    TokenPairSerializer,
)
from rest_framework import serializers

from apps.authentication.models import RootUser
from apps.authentication.services import create_organization_jwt_tokens
from apps.organization.models import Organization


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(read_only=True)

    class Meta:
        model = RootUser
        fields = ("id", "first_name", "last_name", "email", "is_active")


class TokenObtainPairSerializer(BaseTokenObtainPairSerializer):
    def get_tokens(self):
        default_organization = Organization.objects.filter(
            organizationpolicy__organizationrole__organization_role_user__root_user=self.user,
        ).first()
        default_organization_slug = (
            default_organization.slug_name if default_organization else None
        )
        refresh_token, access_token = create_organization_jwt_tokens(
            self.user, organization_slug=default_organization_slug
        )

        return refresh_token, access_token, default_organization_slug

    def get_response_data(self):
        refresh_token, access_token, default_organization = self.get_tokens()

        return {
            "refresh": str(refresh_token),
            "access": str(access_token),
            "default_organization": default_organization,
        }


class AuthTokenPairSerializer(TokenPairSerializer):
    default_organization = serializers.CharField()


class OrganizationTokenRefreshSerializer(CustomTokenRefreshSerializer):
    organization = serializers.CharField(write_only=True, allow_null=True)


class SendEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class ForgetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, write_only=True
    )
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value: str):
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError(
                "This new password must contain at least 1 digit."
            )
        if all(char.isalnum() for char in value):
            raise serializers.ValidationError(
                "This new password must contain at least 1 special letter"
            )
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError(
                "This new password must contain at least 1 upper case letter"
            )
        if not any(char.islower() for char in value):
            raise serializers.ValidationError(
                "This new password must contain at least 1 lower case letter"
            )
        return value

    def update(self, instance, validated_data):
        current_password = validated_data.get("password")
        new_password = validated_data.get("new_password")

        if instance.has_usable_password():
            if not current_password:
                raise serializers.ValidationError(
                    {"password": "Current password is required."}
                )
            if not instance.check_password(current_password):
                raise serializers.ValidationError(
                    {"error": "Current password is incorrect"}
                )
            if current_password == new_password:
                raise serializers.ValidationError(
                    {"error": "New password cannot be the same as the current password"}
                )

        instance.set_password(new_password)
        instance.save()
        return instance
