"""Opt-in smoke test against real AWS.

Skipped by default. Enable with `RUN_REAL_AWS_TESTS=1` plus a working
SSO session (`aws sso login --profile cx9-gmail`). Costs roughly
$0.04 per run (one Stability Image Core invocation) and writes one
PNG to `S3_GENERATED_BUCKET`.
"""

import base64
import json
import os
import uuid

import boto3
import pytest

REGION = "us-west-2"
MODEL_ID = "stability.stable-image-core-v1:1"
BUCKET = os.environ.get("S3_GENERATED_BUCKET", "photo-feed-generated-usw2")


@pytest.mark.skipif(
    os.environ.get("RUN_REAL_AWS_TESTS") != "1",
    reason="Real-AWS test; set RUN_REAL_AWS_TESTS=1 to enable.",
)
def test_real_bedrock_returns_png() -> None:
    session = boto3.Session(profile_name=os.environ.get("AWS_PROFILE", "cx9-gmail"))
    bedrock = session.client("bedrock-runtime", region_name=REGION)
    s3 = session.client("s3", region_name=REGION)

    job_id = f"smoke-{uuid.uuid4().hex[:8]}"
    body = json.dumps(
        {
            "prompt": "a red apple on a white table, studio photo",
            "mode": "text-to-image",
            "aspect_ratio": "1:1",
            "output_format": "png",
        }
    ).encode()
    resp = bedrock.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=body,
    )
    payload = json.loads(resp["body"].read())
    assert payload["finish_reasons"][0] is None, payload["finish_reasons"]
    assert payload["images"], "no images in response"

    png = base64.b64decode(payload["images"][0])
    assert png.startswith(b"\x89PNG"), "result is not a PNG"
    key = f"{job_id}/0.png"
    s3.put_object(Bucket=BUCKET, Key=key, Body=png, ContentType="image/png")
    head = s3.head_object(Bucket=BUCKET, Key=key)
    assert head["ContentType"] == "image/png"
    assert head["ContentLength"] > 10_000  # real PNG, not a placeholder
