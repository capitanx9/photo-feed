import uuid

import boto3
from botocore.config import Config
from django.conf import settings

# ======================================================================
# Client
# ======================================================================


def _client_kwargs(region: str, *, public: bool = False) -> dict[str, object]:
    """Common boto3.client kwargs. In dev AWS_S3_ENDPOINT_URL points to MinIO,
    which requires path-style addressing (Bucket as URL path, not subdomain).

    Two flavours: `public=False` for server-side ops (put/get) — uses the
    in-cluster hostname, fast and inside the docker network. `public=True`
    for presign — uses the browser-facing URL so the signed `host` header
    matches what the browser actually requests."""
    kwargs: dict[str, object] = {"region_name": region}
    endpoint = (
        settings.AWS_S3_PUBLIC_ENDPOINT_URL
        if public and settings.AWS_S3_PUBLIC_ENDPOINT_URL
        else settings.AWS_S3_ENDPOINT_URL
    )
    if endpoint:
        kwargs["endpoint_url"] = endpoint
        kwargs["config"] = Config(signature_version="s3v4", s3={"addressing_style": "path"})
    return kwargs


def get_s3_client():  # type: ignore[no-untyped-def]
    """Server-side S3 client (used for put_object / head_object inside Django)."""
    return boto3.client("s3", **_client_kwargs(settings.AWS_REGION))


def get_s3_presigner():  # type: ignore[no-untyped-def]
    """Browser-facing S3 client used only to mint presigned URLs."""
    return boto3.client("s3", **_client_kwargs(settings.AWS_REGION, public=True))


def get_generated_s3_client():  # type: ignore[no-untyped-def]
    return boto3.client("s3", **_client_kwargs(settings.S3_GENERATED_REGION))


def get_generated_s3_presigner():  # type: ignore[no-untyped-def]
    return boto3.client("s3", **_client_kwargs(settings.S3_GENERATED_REGION, public=True))


# ======================================================================
# Key helpers
# ======================================================================


def make_raw_key(user_id: int, kind: str, extension: str) -> str:
    return f"raw/{kind}s/{user_id}/{uuid.uuid4().hex}.{extension.lstrip('.')}"


# ======================================================================
# Presign
# ======================================================================


def make_upload_presign(*, key: str, content_type: str, content_length: int) -> str:
    # `content_length` is validated *before* presigning (see
    # validate_upload_params) so the bucket can't be filled with
    # arbitrary blobs from the API surface. We deliberately do NOT
    # include ContentLength in the presign params: when boto3 signs it,
    # S3 demands the browser's PUT match the signed value byte-for-byte.
    # The browser sets Content-Length itself from the File object and
    # there's no way for the client to guarantee equality across content
    # encodings or HTTP/2 framing — the result is sporadic 403
    # SignatureDoesNotMatch responses (which is exactly what we hit in
    # prod on the first end-to-end upload). Dropping ContentLength leaves
    # only ContentType as the cross-checked field; size validation stays
    # on the application side where it belongs.
    del content_length  # kept in the signature for callers; ignored here
    url: str = get_s3_presigner().generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.S3_UPLOADS_BUCKET,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=settings.S3_PRESIGN_TTL_SECONDS,
    )
    return url


def make_download_presign(*, key: str) -> str:
    url: str = get_s3_presigner().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_UPLOADS_BUCKET, "Key": key},
        ExpiresIn=settings.S3_PRESIGN_TTL_SECONDS,
    )
    return url


def make_download_presign_for_generated(*, key: str) -> str:
    url: str = get_generated_s3_presigner().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_GENERATED_BUCKET, "Key": key},
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
