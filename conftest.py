"""Pytest bootstrap.

api tests need Django settings + a Postgres on localhost. lambda tests
(cut_image, generate_image) are self-contained — the lambda `make test-lambdas`
target uses `-p no:django` to skip the plugin entirely. Env vars below are
fallbacks for ad-hoc `pytest` invocations; the Makefile sets the canonical set.
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
os.environ.setdefault("RATELIMIT_ENABLE", "False")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "1")

# moto + boto3 need *some* AWS creds present in env; values are dummy.
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")  # pragma: allowlist secret
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")  # pragma: allowlist secret
os.environ.setdefault("AWS_DEFAULT_REGION", "eu-west-1")

# Force the in-memory S3 endpoint in tests (moto intercepts boto3 globally).
# The dev .env points at MinIO; we don't want test runs to hit it.
os.environ["AWS_S3_ENDPOINT_URL"] = ""
os.environ["AWS_S3_PUBLIC_ENDPOINT_URL"] = ""
