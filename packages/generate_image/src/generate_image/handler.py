"""Lambda: generate images via Bedrock (Stability AI) and upload to S3.

Invoked synchronously by the Django Celery worker. Designed to live in
us-west-2 — the only AWS region with ACTIVE text-to-image foundation
models (Stability AI). Output bucket lives in the same region so the
multi-megabyte PNG write is a local PUT.
"""

import base64
import json
import logging
import os
import secrets
import time
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# ======================================================================
# Configuration
# ======================================================================

MAX_VARIANTS = 4
ALLOWED_ASPECT_RATIOS = {"1:1", "4:5", "16:9"}
THROTTLING_RETRIES = 3
THROTTLING_BACKOFF_SECONDS = (1.0, 2.0, 4.0)


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


# ======================================================================
# Bedrock invoke
# ======================================================================


def _build_payload(
    *, prompt: str, aspect_ratio: str, seed: int, negative_prompt: str | None
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "prompt": prompt,
        "mode": "text-to-image",
        "aspect_ratio": aspect_ratio,
        "output_format": "png",
        "seed": seed,
    }
    if negative_prompt:
        payload["negative_prompt"] = negative_prompt
    return payload


def _invoke_with_retry(bedrock: Any, *, model_id: str, body: bytes) -> dict[str, Any]:
    """Call invoke_model with backoff on ThrottlingException."""
    for attempt in range(THROTTLING_RETRIES):
        try:
            resp = bedrock.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=body,
            )
            return json.loads(resp["body"].read())
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code != "ThrottlingException" or attempt == THROTTLING_RETRIES - 1:
                raise
            sleep_for = THROTTLING_BACKOFF_SECONDS[attempt]
            logger.warning(
                "ThrottlingException on attempt %d/%d, sleeping %.1fs",
                attempt + 1,
                THROTTLING_RETRIES,
                sleep_for,
            )
            time.sleep(sleep_for)
    # unreachable — loop either returns or raises
    raise RuntimeError("invoke_with_retry: unreachable")


# ======================================================================
# Lambda entrypoint
# ======================================================================


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    job_id = event["job_id"]
    prompt = event["prompt"]
    variants_count = int(event.get("variants_count", 1))
    aspect_ratio = event.get("aspect_ratio", "1:1")
    negative_prompt = event.get("negative_prompt") or None

    if not 1 <= variants_count <= MAX_VARIANTS:
        raise ValueError(f"variants_count must be in [1, {MAX_VARIANTS}], got {variants_count}")
    if aspect_ratio not in ALLOWED_ASPECT_RATIOS:
        raise ValueError(
            f"aspect_ratio must be one of {sorted(ALLOWED_ASPECT_RATIOS)}, got {aspect_ratio!r}"
        )

    model_id = _required_env("BEDROCK_IMAGE_MODEL_ID")
    bucket = _required_env("S3_GENERATED_BUCKET")

    bedrock = boto3.client("bedrock-runtime")
    s3 = boto3.client("s3")

    image_keys: list[str] = []
    seeds: list[int] = []
    for variant_index in range(variants_count):
        seed = secrets.randbits(31)
        body = json.dumps(
            _build_payload(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                seed=seed,
                negative_prompt=negative_prompt,
            )
        ).encode()
        payload = _invoke_with_retry(bedrock, model_id=model_id, body=body)

        finish_reason = payload.get("finish_reasons", [None])[0]
        if finish_reason is not None:
            raise RuntimeError(f"Bedrock content filter tripped: {finish_reason}")

        png_bytes = base64.b64decode(payload["images"][0])
        key = f"{job_id}/{variant_index}.png"
        s3.put_object(Bucket=bucket, Key=key, Body=png_bytes, ContentType="image/png")
        image_keys.append(key)
        seeds.append(seed)
        logger.info("generated s3://%s/%s (seed=%d)", bucket, key, seed)

    return {"image_keys": image_keys, "seeds": seeds}
