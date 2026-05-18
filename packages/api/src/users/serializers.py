from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User

# ======================================================================
# Register
# ======================================================================


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["id", "email", "password"]
        read_only_fields = ["id"]

    def create(self, validated_data: dict) -> User:  # type: ignore[type-arg]
        user: User = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user


# ======================================================================
# User payload
# ======================================================================


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email"]
        read_only_fields = ["id", "email"]


# ======================================================================
# Login
# ======================================================================


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
