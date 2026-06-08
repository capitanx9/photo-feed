import base64
import json
from io import BytesIO
from typing import Any

import boto3
import pytest
from botocore.exceptions import ClientError
from generate_image import handler
from moto import mock_aws

BUCKET = "photo-feed-generated-usw2"
MODEL_ID = "stability.stable-image-core-v1:1"
JOB_ID = "00000000-0000-0000-0000-000000000001"


# ======================================================================
# Fixtures
# ======================================================================


@pytest.fixture(autouse=True)
def lambda_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BEDROCK_IMAGE_MODEL_ID", MODEL_ID)
    monkeypatch.setenv("S3_GENERATED_BUCKET", BUCKET)
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-west-2")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")  # pragma: allowlist secret
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")  # pragma: allowlist secret


@pytest.fixture(autouse=True)
def no_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(handler.time, "sleep", lambda _s: None)


def _png_payload(finish_reason: str | None = None) -> dict[str, Any]:
    # 1x1 transparent PNG
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
        "890000000d49444154789c63000100000005000100"
        "0d0a2db40000000049454e44ae426082"
    )
    return {
        "images": [base64.b64encode(png).decode()],
        "seeds": [42],
        "finish_reasons": [finish_reason],
    }


def _make_bedrock_stub(payloads: list[dict[str, Any] | Exception]) -> Any:
    """Returns a fake bedrock client whose invoke_model walks `payloads`."""
    calls: list[dict[str, Any]] = []

    class _Stub:
        def invoke_model(self, **kwargs: Any) -> dict[str, Any]:
            calls.append(kwargs)
            next_item = payloads.pop(0)
            if isinstance(next_item, Exception):
                raise next_item
            return {"body": BytesIO(json.dumps(next_item).encode())}

    stub = _Stub()
    stub.calls = calls  # type: ignore[attr-defined]
    return stub


def _patch_bedrock(monkeypatch: pytest.MonkeyPatch, stub: Any) -> None:
    real_client = boto3.client

    def fake_client(service: str, *args: Any, **kwargs: Any) -> Any:
        if service == "bedrock-runtime":
            return stub
        return real_client(service, *args, **kwargs)

    monkeypatch.setattr(handler.boto3, "client", fake_client)


def _create_bucket() -> Any:
    s3 = boto3.client("s3", region_name="us-west-2")
    s3.create_bucket(
        Bucket=BUCKET,
        CreateBucketConfiguration={"LocationConstraint": "us-west-2"},
    )
    return s3


# ======================================================================
# Happy paths
# ======================================================================


@mock_aws
def test_handler_writes_one_variant_to_s3(monkeypatch: pytest.MonkeyPatch) -> None:
    s3 = _create_bucket()
    stub = _make_bedrock_stub([_png_payload()])
    _patch_bedrock(monkeypatch, stub)

    result = handler.lambda_handler(
        {
            "job_id": JOB_ID,
            "prompt": "a red apple on a white table, studio photo",
            "variants_count": 1,
            "aspect_ratio": "1:1",
        },
        None,
    )

    assert result["image_keys"] == [f"{JOB_ID}/0.png"]
    assert len(result["seeds"]) == 1
    head = s3.head_object(Bucket=BUCKET, Key=f"{JOB_ID}/0.png")
    assert head["ContentType"] == "image/png"
    assert len(stub.calls) == 1
    sent = json.loads(stub.calls[0]["body"])
    assert sent["prompt"].startswith("a red apple")
    assert sent["mode"] == "text-to-image"
    assert sent["aspect_ratio"] == "1:1"
    assert sent["output_format"] == "png"


@mock_aws
def test_handler_writes_multiple_variants(monkeypatch: pytest.MonkeyPatch) -> None:
    s3 = _create_bucket()
    stub = _make_bedrock_stub([_png_payload(), _png_payload(), _png_payload()])
    _patch_bedrock(monkeypatch, stub)

    result = handler.lambda_handler(
        {"job_id": JOB_ID, "prompt": "x", "variants_count": 3, "aspect_ratio": "4:5"},
        None,
    )

    assert result["image_keys"] == [
        f"{JOB_ID}/0.png",
        f"{JOB_ID}/1.png",
        f"{JOB_ID}/2.png",
    ]
    assert len({r["seeds"] for r in [{"seeds": tuple(result["seeds"])}]}) == 1
    assert len(set(result["seeds"])) == 3  # secrets gives distinct seeds in practice
    # bucket got 3 objects
    listed = s3.list_objects_v2(Bucket=BUCKET, Prefix=f"{JOB_ID}/")
    assert listed["KeyCount"] == 3


@mock_aws
def test_handler_forwards_negative_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    _create_bucket()
    stub = _make_bedrock_stub([_png_payload()])
    _patch_bedrock(monkeypatch, stub)

    handler.lambda_handler(
        {
            "job_id": JOB_ID,
            "prompt": "x",
            "variants_count": 1,
            "aspect_ratio": "1:1",
            "negative_prompt": "blurry, low quality",
        },
        None,
    )

    sent = json.loads(stub.calls[0]["body"])
    assert sent["negative_prompt"] == "blurry, low quality"


# ======================================================================
# Failure modes
# ======================================================================


@mock_aws
def test_handler_raises_on_content_filter(monkeypatch: pytest.MonkeyPatch) -> None:
    _create_bucket()
    stub = _make_bedrock_stub([_png_payload(finish_reason="CONTENT_FILTERED")])
    _patch_bedrock(monkeypatch, stub)

    with pytest.raises(RuntimeError, match="content filter"):
        handler.lambda_handler(
            {"job_id": JOB_ID, "prompt": "x", "variants_count": 1, "aspect_ratio": "1:1"},
            None,
        )


@mock_aws
def test_handler_retries_on_throttling(monkeypatch: pytest.MonkeyPatch) -> None:
    s3 = _create_bucket()
    throttle = ClientError(
        {"Error": {"Code": "ThrottlingException", "Message": "Slow down"}}, "InvokeModel"
    )
    stub = _make_bedrock_stub([throttle, _png_payload()])
    _patch_bedrock(monkeypatch, stub)

    result = handler.lambda_handler(
        {"job_id": JOB_ID, "prompt": "x", "variants_count": 1, "aspect_ratio": "1:1"},
        None,
    )

    assert result["image_keys"] == [f"{JOB_ID}/0.png"]
    assert len(stub.calls) == 2
    s3.head_object(Bucket=BUCKET, Key=f"{JOB_ID}/0.png")  # exists


@mock_aws
def test_handler_gives_up_after_throttling_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    _create_bucket()
    throttle = ClientError(
        {"Error": {"Code": "ThrottlingException", "Message": "Slow down"}}, "InvokeModel"
    )
    stub = _make_bedrock_stub([throttle, throttle, throttle])
    _patch_bedrock(monkeypatch, stub)

    with pytest.raises(ClientError):
        handler.lambda_handler(
            {"job_id": JOB_ID, "prompt": "x", "variants_count": 1, "aspect_ratio": "1:1"},
            None,
        )
    assert len(stub.calls) == 3


def test_handler_rejects_bad_variants_count() -> None:
    with pytest.raises(ValueError, match=r"variants_count must be in \[1, 4\]"):
        handler.lambda_handler(
            {"job_id": JOB_ID, "prompt": "x", "variants_count": 5, "aspect_ratio": "1:1"},
            None,
        )


def test_handler_rejects_bad_aspect_ratio() -> None:
    with pytest.raises(ValueError, match="aspect_ratio"):
        handler.lambda_handler(
            {"job_id": JOB_ID, "prompt": "x", "variants_count": 1, "aspect_ratio": "9:21"},
            None,
        )


def test_handler_propagates_when_model_id_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BEDROCK_IMAGE_MODEL_ID")
    with pytest.raises(RuntimeError, match="BEDROCK_IMAGE_MODEL_ID"):
        handler.lambda_handler(
            {"job_id": JOB_ID, "prompt": "x", "variants_count": 1, "aspect_ratio": "1:1"},
            None,
        )
