"""Shared Django settings — env-agnostic defaults."""

from datetime import timedelta
from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


# ======================================================================
# Core
# ======================================================================

SECRET_KEY = config("DJANGO_SECRET_KEY")
DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=Csv())


# ======================================================================
# Apps + middleware
# ======================================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "corsheaders",
    "users",
    "posts",
    "orders",
    "ai",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ======================================================================
# URLs + templates + WSGI
# ======================================================================

ROOT_URLCONF = "api.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "api.wsgi.application"


# ======================================================================
# Database
# ======================================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB"),
        "USER": config("POSTGRES_USER"),
        "PASSWORD": config("POSTGRES_PASSWORD"),
        "HOST": config("POSTGRES_HOST"),
        "PORT": config("POSTGRES_PORT", default="5432"),
    }
}


# ======================================================================
# Auth model + password validators
# ======================================================================

AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ======================================================================
# i18n + static
# ======================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ======================================================================
# DRF + SimpleJWT
# ======================================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["users.auth.CookieJWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "photo-feed API",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SORT_OPERATIONS": False,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}


# ======================================================================
# Auth cookies
# ======================================================================

ACCESS_TOKEN_COOKIE = "access_token"
REFRESH_TOKEN_COOKIE = "refresh_token"
AUTH_COOKIE_SAMESITE = "Lax"
AUTH_COOKIE_SECURE = config("AUTH_COOKIE_SECURE", default=not DEBUG, cast=bool)


# ======================================================================
# CORS + CSRF
# ======================================================================

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://127.0.0.1:3000",
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="http://localhost:3000,http://127.0.0.1:3000",
    cast=Csv(),
)
CSRF_COOKIE_HTTPONLY = False  # frontend reads it to populate X-CSRFToken header
CSRF_COOKIE_SAMESITE = "Lax"


# ======================================================================
# AWS / S3 uploads
# ======================================================================

AWS_REGION = config("AWS_REGION", default="eu-west-1")
S3_UPLOADS_BUCKET = config("S3_UPLOADS_BUCKET", default="photo-feed-uploads")
S3_PRESIGN_TTL_SECONDS = config("S3_PRESIGN_TTL_SECONDS", default=300, cast=int)
UPLOAD_MAX_BYTES = config("UPLOAD_MAX_BYTES", default=10 * 1024 * 1024, cast=int)
UPLOAD_ALLOWED_MIME = ["image/jpeg", "image/png", "image/webp"]

WEBHOOK_SHARED_SECRET = config("WEBHOOK_SHARED_SECRET", default="local-dev-secret")


# ======================================================================
# Rate limiting
# ======================================================================

RATELIMIT_ENABLE = config("RATELIMIT_ENABLE", default=True, cast=bool)


# ======================================================================
# AI / Bedrock image generation
# ======================================================================
#
# The generate_image Lambda + its output bucket live in us-west-2 because
# Bedrock text-to-image is only ACTIVE there (Stability AI). EC2/Django run
# in eu-central-1; Celery boto3-invokes the Lambda cross-region, the user
# downloads the PNG via a presigned GET against the us-west-2 bucket.

BEDROCK_REGION = config("BEDROCK_REGION", default="us-west-2")
GENERATE_IMAGE_LAMBDA_NAME = config(
    "GENERATE_IMAGE_LAMBDA_NAME",
    default="photo-feed-generate-image",
)
S3_GENERATED_BUCKET = config("S3_GENERATED_BUCKET", default="photo-feed-generated-usw2")
S3_GENERATED_REGION = config("S3_GENERATED_REGION", default="us-west-2")

AI_RATE_LIMIT_PER_HOUR = config("AI_RATE_LIMIT_PER_HOUR", default=10, cast=int)
AI_MAX_VARIANTS = 4
AI_ALLOWED_ASPECT_RATIOS = ["1:1", "4:5", "16:9"]

REDIS_URL = config("REDIS_URL", default="redis://localhost:6379/2")
