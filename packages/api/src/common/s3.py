import uuid

import boto3
from django.conf import settings

# ======================================================================
# Client
# ======================================================================


def get_s3_client():  # type: ignore[no-untyped-def]
    return boto3.client("s3", region_name=settings.AWS_REGION)


# ======================================================================
# Key helpers
# ======================================================================


def make_raw_key(user_id: int, kind: str, extension: str) -> str:
    return f"raw/{kind}s/{user_id}/{uuid.uuid4().hex}.{extension.lstrip('.')}"


# ======================================================================
# Presign
# ======================================================================


def make_upload_presign(*, key: str, content_type: str, content_length: int) -> str:
    url: str = get_s3_client().generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.S3_UPLOADS_BUCKET,
            "Key": key,
            "ContentType": content_type,
            "ContentLength": content_length,
        },
        ExpiresIn=settings.S3_PRESIGN_TTL_SECONDS,
    )
    return url


def make_download_presign(*, key: str) -> str:
    url: str = get_s3_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_UPLOADS_BUCKET, "Key": key},
        ExpiresIn=settings.S3_PRESIGN_TTL_SECONDS,
    )
    return url


# ======================================================================
# Mime / size guards
# ======================================================================

EXT_BY_MIME = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


def validate_upload_params(*, content_type: str, content_length: int) -> str:
    if content_type not in settings.UPLOAD_ALLOWED_MIME:
        raise ValueError(f"content_type must be one of {settings.UPLOAD_ALLOWED_MIME}")
    if content_length <= 0 or content_length > settings.UPLOAD_MAX_BYTES:
        raise ValueError(
            f"content_length must be in (0, {settings.UPLOAD_MAX_BYTES}], got {content_length}"
        )
    return EXT_BY_MIME[content_type]
