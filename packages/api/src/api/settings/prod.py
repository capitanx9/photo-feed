"""Production settings — used on EC2."""

from decouple import Csv

from .base import *
from .base import config

DEBUG = False

# ======================================================================
# Hosts / CSRF / CORS — driven by env (set by entrypoint from SSM)
# ======================================================================
#
# ALLOWED_HOSTS: comma-separated DNS names that may serve the app.
# CSRF_TRUSTED_ORIGINS / CORS_ALLOWED_ORIGINS: full origins with scheme.

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", cast=Csv())
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", cast=Csv())


# ======================================================================
# Cookies / TLS
# ======================================================================

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
AUTH_COOKIE_SECURE = True
AUTH_COOKIE_SAMESITE = "Lax"

# Trust the X-Forwarded-Proto header set by nginx so request.is_secure()
# returns True behind the TLS-terminating proxy.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# ======================================================================
# Logging — to stdout so `docker logs web` captures everything
# ======================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django.db.backends": {"level": "WARNING"},
        "botocore": {"level": "WARNING"},
        "boto3": {"level": "WARNING"},
    },
}
