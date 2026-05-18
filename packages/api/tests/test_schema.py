import yaml
from django.urls import reverse
from rest_framework.test import APIClient

# ======================================================================
# Schema endpoint
# ======================================================================


def test_schema_endpoint_returns_valid_yaml() -> None:
    resp = APIClient().get(reverse("schema"))
    assert resp.status_code == 200
    parsed = yaml.safe_load(resp.content)
    assert parsed["openapi"].startswith("3.")
    assert parsed["info"]["title"] == "photo-feed API"


# ======================================================================
# Coverage
# ======================================================================


def test_schema_lists_every_endpoint() -> None:
    resp = APIClient().get(reverse("schema"))
    parsed = yaml.safe_load(resp.content)
    paths = set(parsed["paths"].keys())
    expected = {
        "/api/health/",
        "/api/auth/register/",
        "/api/auth/login/",
        "/api/auth/logout/",
        "/api/auth/refresh/",
        "/api/auth/me/",
        "/api/users/{id}/",
        "/api/users/{id}/posts/",
        "/api/posts/",
        "/api/posts/{id}/",
        "/api/posts/upload-url/",
        "/api/posts/media/{id}/",
        "/internal/media/{id}/processed/",
    }
    assert expected <= paths, f"missing: {expected - paths}"


# ======================================================================
# Tags + error envelope
# ======================================================================


def test_auth_endpoints_share_tag_and_error_shape() -> None:
    resp = APIClient().get(reverse("schema"))
    parsed = yaml.safe_load(resp.content)
    for path in ("/api/auth/login/", "/api/auth/register/"):
        op = parsed["paths"][path]["post"]
        assert op["tags"] == ["auth"]
        # every documented 4xx response must point at the shared Error schema
        for code in ("400", "401", "429"):
            if code in op["responses"]:
                schema_ref = op["responses"][code]["content"]["application/json"]["schema"]
                assert schema_ref == {"$ref": "#/components/schemas/Error"}
