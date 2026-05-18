"""Pytest bootstrap — populates env vars before Django settings load.

Tests require a real Postgres. The Makefile and the CI workflow both set
POSTGRES_HOST=localhost before invoking pytest, so the values below are only
fallbacks for ad-hoc `pytest` invocations.
"""

import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret")  # pragma: allowlist secret
os.environ.setdefault("DJANGO_DEBUG", "1")
os.environ.setdefault("ALLOWED_HOSTS", "testserver")
os.environ.setdefault("POSTGRES_DB", "api")
os.environ.setdefault("POSTGRES_USER", "api")
os.environ.setdefault("POSTGRES_PASSWORD", "api")  # pragma: allowlist secret
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")

# moto + boto3 need *some* AWS creds present in env; values are dummy.
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")  # pragma: allowlist secret
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")  # pragma: allowlist secret
os.environ.setdefault("AWS_DEFAULT_REGION", "eu-west-1")


def pytest_configure(config) -> None:  # type: ignore[no-untyped-def]
    from django.conf import settings

    # Tests would otherwise share the 5/min and 10/min per-IP rate limits.
    settings.RATELIMIT_ENABLE = False
