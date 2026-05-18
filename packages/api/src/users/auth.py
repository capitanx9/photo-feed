"""DRF authentication class that reads the JWT from an HttpOnly cookie."""

from django.conf import settings
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request: Request):  # type: ignore[override]
        raw_token = request.COOKIES.get(settings.ACCESS_TOKEN_COOKIE)
        if raw_token is None:
            return None
        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
