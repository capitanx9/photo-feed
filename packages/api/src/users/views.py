import contextlib

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .cookies import clear_auth_cookies, set_auth_cookies
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer

User = get_user_model()


# ======================================================================
# Helpers
# ======================================================================


def _issue_tokens(user) -> tuple[str, str]:  # type: ignore[no-untyped-def]
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)


# ======================================================================
# Register
# ======================================================================


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key="ip", rate="5/m", method="POST", block=True))
    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


# ======================================================================
# Login
# ======================================================================


class LoginView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key="ip", rate="10/m", method="POST", block=True))
    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response(
                {"detail": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        access, refresh = _issue_tokens(user)
        response = Response(UserSerializer(user).data, status=status.HTTP_200_OK)
        return set_auth_cookies(response, access, refresh)


# ======================================================================
# Logout
# ======================================================================


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        raw_refresh = request.COOKIES.get(settings.REFRESH_TOKEN_COOKIE)
        if raw_refresh:
            with contextlib.suppress(TokenError):
                RefreshToken(raw_refresh).blacklist()
        response = Response(status=status.HTTP_204_NO_CONTENT)
        return clear_auth_cookies(response)


# ======================================================================
# Refresh
# ======================================================================


class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        raw_refresh = request.COOKIES.get(settings.REFRESH_TOKEN_COOKIE)
        if not raw_refresh:
            return Response({"detail": "No refresh token"}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            old_refresh = RefreshToken(raw_refresh)
            user_id = old_refresh["user_id"]
            old_refresh.blacklist()
        except TokenError:
            return Response(
                {"detail": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED
            )
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED
            )
        new_refresh = RefreshToken.for_user(user)
        access = str(new_refresh.access_token)
        refresh = str(new_refresh)
        response = Response(status=status.HTTP_200_OK)
        return set_auth_cookies(response, access, refresh)


# ======================================================================
# Me
# ======================================================================


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(UserSerializer(request.user).data)
