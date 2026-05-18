from io import BytesIO
from typing import Any

import boto3
import pytest
import responses
from cut_image import handler
from moto import mock_aws
from PIL import Image

BUCKET = "photo-feed-uploads"
RAW_KEY = "raw/posts/1/example.jpg"
RESIZED_KEY = "resized/posts/1/example.jpg"
DJANGO_URL = "http://django.test"
SECRET = "lambda-secret"  # pragma: allowlist secret


# ======================================================================
# Fixtures
# ======================================================================

# === env vars for handler ===


@pytest.fixture(autouse=True)
def lambda_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DJANGO_URL", DJANGO_URL)
    monkeypatch.setenv("WEBHOOK_SHARED_SECRET", SECRET)
    monkeypatch.setenv("AWS_DEFAULT_REGION", "eu-west-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")  # pragma: allowlist secret
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")  # pragma: allowlist secret


# === sample event ===


@pytest.fixture
def s3_event() -> dict:  # type: ignore[type-arg]
    return {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": BUCKET},
                    "object": {"key": RAW_KEY},
                }
            }
        ]
    }


# === seeded bucket with one image ===


def _put_jpeg(client: Any, bucket: str, key: str, size: tuple[int, int] = (2000, 1500)) -> None:
    buf = BytesIO()
    Image.new("RGB", size, color=(127, 200, 50)).save(buf, format="JPEG")
    client.put_object(Bucket=bucket, Key=key, Body=buf.getvalue(), ContentType="image/jpeg")


# ======================================================================
# Image processing
# ======================================================================


def test_resize_to_square_outputs_1080_jpeg() -> None:
    buf = BytesIO()
    Image.new("RGB", (3000, 1000), color=(10, 20, 30)).save(buf, format="JPEG")
    out = handler.resize_to_square(buf.getvalue())
    result = Image.open(BytesIO(out))
    assert result.size == (1080, 1080)
    assert result.format == "JPEG"


# ======================================================================
# Lambda entrypoint
# ======================================================================


@mock_aws
@responses.activate
def test_handler_resizes_and_notifies_django(s3_event: dict) -> None:  # type: ignore[type-arg]
    client = boto3.client("s3", region_name="eu-west-1")
    client.create_bucket(
        Bucket=BUCKET,
        CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
    )
    _put_jpeg(client, BUCKET, RAW_KEY)
    responses.add(
        responses.POST,
        f"{DJANGO_URL}/internal/media/processed/",
        status=204,
    )

    result = handler.lambda_handler(s3_event, None)

    assert result == {"processed": 1}
    head = client.head_object(Bucket=BUCKET, Key=RESIZED_KEY)
    assert head["ContentType"] == "image/jpeg"
    assert len(responses.calls) == 1
    call_body = responses.calls[0].request.body
    assert b'"s3_key": "raw/posts/1/example.jpg"' in call_body
    assert b'"status": "ready"' in call_body
    assert responses.calls[0].request.headers["X-Lambda-Token"] == SECRET


@mock_aws
@responses.activate
def test_handler_reports_failed_status_when_resize_blows_up(
    s3_event: dict,  # type: ignore[type-arg]
) -> None:
    client = boto3.client("s3", region_name="eu-west-1")
    client.create_bucket(
        Bucket=BUCKET,
        CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
    )
    # not a real image — Pillow will fail
    client.put_object(Bucket=BUCKET, Key=RAW_KEY, Body=b"not an image")
    responses.add(
        responses.POST,
        f"{DJANGO_URL}/internal/media/processed/",
        status=204,
    )

    with pytest.raises(Image.UnidentifiedImageError):
        handler.lambda_handler(s3_event, None)

    assert len(responses.calls) == 1
    assert b'"status": "failed"' in responses.calls[0].request.body


def test_resized_key_rejects_non_raw_input() -> None:
    with pytest.raises(ValueError, match="Expected key under raw/"):
        handler._resized_key("something/else.jpg")


def test_handler_propagates_when_secret_missing(
    s3_event: dict, monkeypatch: pytest.MonkeyPatch
) -> None:  # type: ignore[type-arg]
    monkeypatch.delenv("WEBHOOK_SHARED_SECRET")
    with mock_aws():
        client = boto3.client("s3", region_name="eu-west-1")
        client.create_bucket(
            Bucket=BUCKET,
            CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
        )
        _put_jpeg(client, BUCKET, RAW_KEY)
        with pytest.raises(RuntimeError, match="WEBHOOK_SHARED_SECRET"):
            handler.lambda_handler(s3_event, None)
