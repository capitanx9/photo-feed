from typing import Any

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

User = get_user_model()

PASSWORD = "sup3rsecret!"  # pragma: allowlist secret
EMAIL = "alice@example.com"


# ======================================================================
# Fixtures
# ======================================================================

# === api client ===


@pytest.fixture
def api() -> APIClient:
    return APIClient(enforce_csrf_checks=False)


# === seeded user ===


@pytest.fixture
def user(db) -> Any:  # type: ignore[no-untyped-def]
    return User.objects.create_user(email=EMAIL, password=PASSWORD)


# ======================================================================
# Register
# ======================================================================


@pytest.mark.django_db
def test_register_creates_user_with_hashed_password(api: APIClient) -> None:
    resp = api.post(
        reverse("register"),
        data={"email": EMAIL, "password": PASSWORD},
        format="json",
    )
    assert resp.status_code == 201
    assert resp.json()["email"] == EMAIL
    created = User.objects.get(email=EMAIL)
    assert created.password != PASSWORD
    assert created.check_password(PASSWORD)


@pytest.mark.django_db
def test_register_rejects_weak_password(api: APIClient) -> None:
    resp = api.post(
        reverse("register"),
        data={"email": EMAIL, "password": "123"},
        format="json",
    )
    assert resp.status_code == 400
    assert "password" in resp.json()


# ======================================================================
# Login
# ======================================================================


@pytest.mark.django_db
def test_login_sets_httponly_cookies(api: APIClient, user: Any) -> None:
    resp = api.post(
        reverse("login"),
        data={"email": EMAIL, "password": PASSWORD},
        format="json",
    )
    assert resp.status_code == 200
    access = resp.cookies[settings.ACCESS_TOKEN_COOKIE]
    refresh = resp.cookies[settings.REFRESH_TOKEN_COOKIE]
    assert access["httponly"] is True
    assert access["samesite"] == "Lax"
    assert access["path"] == "/"
    assert refresh["httponly"] is True
    assert refresh["samesite"] == "Lax"
    assert refresh["path"] == "/api/auth/"


@pytest.mark.django_db
def test_login_wrong_password_returns_401_and_no_cookies(api: APIClient, user: Any) -> None:
    resp = api.post(
        reverse("login"),
        data={"email": EMAIL, "password": "wrong"},  # pragma: allowlist secret
        format="json",
    )
    assert resp.status_code == 401
    assert settings.ACCESS_TOKEN_COOKIE not in resp.cookies
    assert settings.REFRESH_TOKEN_COOKIE not in resp.cookies


# ======================================================================
# Me
# ======================================================================


@pytest.mark.django_db
def test_me_requires_auth(api: APIClient) -> None:
    resp = api.get(reverse("me"))
    assert resp.status_code == 401


@pytest.mark.django_db
def test_me_returns_current_user(api: APIClient, user: Any) -> None:
    login = api.post(
        reverse("login"),
        data={"email": EMAIL, "password": PASSWORD},
        format="json",
    )
    assert login.status_code == 200
    me = api.get(reverse("me"))
    assert me.status_code == 200
    assert me.json() == {"id": user.id, "email": EMAIL}


# ======================================================================
# Refresh
# ======================================================================


@pytest.mark.django_db
def test_refresh_rotates_and_blacklists_old(api: APIClient, user: Any) -> None:
    api.post(
        reverse("login"),
        data={"email": EMAIL, "password": PASSWORD},
        format="json",
    )
    old_refresh = api.cookies[settings.REFRESH_TOKEN_COOKIE].value
    resp = api.post(reverse("refresh"))
    assert resp.status_code == 200
    new_refresh = resp.cookies[settings.REFRESH_TOKEN_COOKIE].value
    assert new_refresh != old_refresh
    api.cookies.clear()
    api.cookies[settings.REFRESH_TOKEN_COOKIE] = old_refresh
    replay = api.post(reverse("refresh"))
    assert replay.status_code == 401


@pytest.mark.django_db
def test_refresh_without_cookie_returns_401(api: APIClient) -> None:
    resp = api.post(reverse("refresh"))
    assert resp.status_code == 401


# ======================================================================
# Logout
# ======================================================================


@pytest.mark.django_db
def test_logout_clears_cookies_and_blacklists_refresh(api: APIClient, user: Any) -> None:
    login = api.post(
        reverse("login"),
        data={"email": EMAIL, "password": PASSWORD},
        format="json",
    )
    refresh = login.cookies[settings.REFRESH_TOKEN_COOKIE].value
    resp = api.post(reverse("logout"))
    assert resp.status_code == 204
    assert resp.cookies[settings.ACCESS_TOKEN_COOKIE].value == ""
    assert resp.cookies[settings.REFRESH_TOKEN_COOKIE].value == ""
    api.cookies.clear()
    api.cookies[settings.REFRESH_TOKEN_COOKIE] = refresh
    again = api.post(reverse("refresh"))
    assert again.status_code == 401
