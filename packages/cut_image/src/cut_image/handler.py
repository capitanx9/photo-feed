"""S3-triggered Lambda: resize an uploaded image and notify Django."""

import logging
import os
from io import BytesIO
from typing import Any

import boto3
import requests
from PIL import Image, ImageOps

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# ======================================================================
# Configuration
# ======================================================================

TARGET_SIZE = 1080
JPEG_QUALITY = 85
WEBHOOK_TIMEOUT_SECONDS = 10


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


# ======================================================================
# Image processing
# ======================================================================


def resize_to_square(raw_bytes: bytes) -> bytes:
    img = Image.open(BytesIO(raw_bytes))
    img = ImageOps.exif_transpose(img)
    img = ImageOps.fit(img, (TARGET_SIZE, TARGET_SIZE), method=Image.Resampling.LANCZOS)
    out = BytesIO()
    img.convert("RGB").save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return out.getvalue()


# ======================================================================
# S3 + webhook glue
# ======================================================================


def _resized_key(raw_key: str) -> str:
    if not raw_key.startswith("raw/"):
        raise ValueError(f"Expected key under raw/, got: {raw_key}")
    return "resized/" + raw_key[len("raw/") :]


def _notify_django(*, s3_key: str, s3_key_resized: str, status: str) -> None:
    url = _required_env("DJANGO_URL").rstrip("/") + "/internal/media/processed/"
    token = _required_env("WEBHOOK_SHARED_SECRET")
    resp = requests.post(
        url,
        json={"s3_key": s3_key, "s3_key_resized": s3_key_resized, "status": status},
        headers={"X-Lambda-Token": token},
        timeout=WEBHOOK_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()


def _process_record(s3: Any, bucket: str, key: str) -> None:
    logger.info("processing s3://%s/%s", bucket, key)
    try:
        raw_obj = s3.get_object(Bucket=bucket, Key=key)
        resized_bytes = resize_to_square(raw_obj["Body"].read())
        resized_key = _resized_key(key)
        s3.put_object(
            Bucket=bucket,
            Key=resized_key,
            Body=resized_bytes,
            ContentType="image/jpeg",
        )
        _notify_django(s3_key=key, s3_key_resized=resized_key, status="ready")
        logger.info("ready: s3://%s/%s", bucket, resized_key)
    except Exception:
        logger.exception("failed to process s3://%s/%s", bucket, key)
        _notify_django(s3_key=key, s3_key_resized="", status="failed")
        raise


# ======================================================================
# Lambda entrypoint
# ======================================================================


def lambda_handler(event: dict, _context: Any) -> dict:  # type: ignore[type-arg]
    s3 = boto3.client("s3")
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        _process_record(s3, bucket, key)
    return {"processed": len(event.get("Records", []))}
