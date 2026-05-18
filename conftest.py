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
