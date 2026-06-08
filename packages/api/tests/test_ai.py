import json
from io import BytesIO
from typing import Any

import pytest
from ai import serializers as ai_serializers
from ai import tasks
from ai.models import GenerationJob
from common import ratelimit
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

User = get_user_model()
PASSWORD = "sup3rsecret!"  # pragma: allowlist secret


# ======================================================================
# Fixtures
# ======================================================================


@pytest.fixture(autouse=True)
def _reset_memory_ratelimit() -> None:
    ratelimit.reset_memory()


@pytest.fixture
def api() -> APIClient:
    return APIClient(enforce_csrf_checks=False)


@pytest.fixture
def alice(db) -> Any:  # type: ignore[no-untyped-def]
    return User.objects.create_user(email="alice@example.com", password=PASSWORD)


@pytest.fixture
def bob(db) -> Any:  # type: ignore[no-untyped-def]
    return User.objects.create_user(email="bob@example.com", password=PASSWORD)


@pytest.fixture
def alice_api(api: APIClient, alice: Any) -> APIClient:
    resp = api.post(
        reverse("auth:login"),
        data={"email": alice.email, "password": PASSWORD},
        format="json",
    )
    assert resp.status_code == 200, resp.content
    return api


@pytest.fixture
def bob_api(bob: Any) -> APIClient:
    fresh = APIClient(enforce_csrf_checks=False)
    resp = fresh.post(
        reverse("auth:login"),
        data={"email": bob.email, "password": PASSWORD},
        format="json",
    )
    assert resp.status_code == 200, resp.content
    return fresh


@pytest.fixture
def mock_lambda_invoke(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Patches boto3.client('lambda') to capture invocations and return canned image keys."""
    captured: dict[str, Any] = {"calls": []}

    class _FakeLambda:
        def invoke(self, **kwargs: Any) -> dict[str, Any]:
            captured["calls"].append(kwargs)
            body = json.dumps({"image_keys": ["1/0.png"], "seeds": [42]}).encode()
            return {"Payload": BytesIO(body)}

    def fake_client(service: str, **kwargs: Any) -> Any:
        if service == "lambda":
            return _FakeLambda()
        raise AssertionError(f"unexpected boto3 service {service}")

    monkeypatch.setattr(tasks.boto3, "client", fake_client)
    return captured


@pytest.fixture
def mock_presign_generated(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        ai_serializers,
        "make_download_presign_for_generated",
        lambda key: f"https://signed.example/{key}",
    )


# ======================================================================
# POST /api/ai/generate/
# ======================================================================


def test_generate_creates_queued_job_and_invokes_lambda(
    alice_api: APIClient,
    alice: Any,
    mock_lambda_invoke: dict[str, Any],
) -> None:
    resp = alice_api.post(
        reverse("ai:generate"),
        data={
            "prompt": "a red apple on a white table, studio photo",
            "variants_count": 1,
            "aspect_ratio": "1:1",
        },
        format="json",
    )

    assert resp.status_code == 202, resp.content
    job_id = resp.json()["job_id"]
    job = GenerationJob.objects.get(pk=job_id)
    # Celery is EAGER in tests — task ran synchronously and finished READY
    assert job.status == GenerationJob.Status.READY
    assert job.image_keys == ["1/0.png"]
    assert job.user_id == alice.id
    # Lambda was invoked exactly once with the right payload
    assert len(mock_lambda_invoke["calls"]) == 1
    sent = json.loads(mock_lambda_invoke["calls"][0]["Payload"])
    assert sent["prompt"].startswith("a red apple")
    assert sent["variants_count"] == 1
    assert sent["aspect_ratio"] == "1:1"
    assert mock_lambda_invoke["calls"][0]["FunctionName"] == "photo-feed-generate-image"
    assert mock_lambda_invoke["calls"][0]["InvocationType"] == "RequestResponse"


def test_generate_rejects_too_many_variants(
    alice_api: APIClient, mock_lambda_invoke: dict[str, Any]
) -> None:
    resp = alice_api.post(
        reverse("ai:generate"),
        data={"prompt": "x", "variants_count": 5, "aspect_ratio": "1:1"},
        format="json",
    )
    assert resp.status_code == 400
    assert "variants_count" in resp.json()
    assert mock_lambda_invoke["calls"] == []


def test_generate_rejects_unknown_aspect_ratio(
    alice_api: APIClient, mock_lambda_invoke: dict[str, Any]
) -> None:
    resp = alice_api.post(
        reverse("ai:generate"),
        data={"prompt": "x", "variants_count": 1, "aspect_ratio": "9:21"},
        format="json",
    )
    assert resp.status_code == 400
    assert "aspect_ratio" in resp.json()


def test_generate_requires_auth(api: APIClient) -> None:
    resp = api.post(
        reverse("ai:generate"),
        data={"prompt": "x", "variants_count": 1, "aspect_ratio": "1:1"},
        format="json",
    )
    assert resp.status_code == 401


def test_generate_rate_limit(
    alice_api: APIClient, settings: Any, mock_lambda_invoke: dict[str, Any]
) -> None:
    settings.AI_RATE_LIMIT_PER_HOUR = 2
    payload = {"prompt": "x", "variants_count": 1, "aspect_ratio": "1:1"}
    assert alice_api.post(reverse("ai:generate"), data=payload, format="json").status_code == 202
    assert alice_api.post(reverse("ai:generate"), data=payload, format="json").status_code == 202
    third = alice_api.post(reverse("ai:generate"), data=payload, format="json")
    assert third.status_code == 429


# ======================================================================
# GET /api/ai/jobs/<id>/
# ======================================================================


def test_job_detail_returns_presigned_urls_when_ready(
    alice_api: APIClient,
    alice: Any,
    mock_presign_generated: None,
) -> None:
    job = GenerationJob.objects.create(
        user=alice,
        prompt="x",
        variants_count=2,
        aspect_ratio="1:1",
        status=GenerationJob.Status.READY,
        image_keys=["3/0.png", "3/1.png"],
    )
    resp = alice_api.get(reverse("ai:job-detail", kwargs={"pk": job.id}))
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["image_urls"] == [
        "https://signed.example/3/0.png",
        "https://signed.example/3/1.png",
    ]


def test_job_detail_empty_urls_when_not_ready(alice_api: APIClient, alice: Any) -> None:
    job = GenerationJob.objects.create(
        user=alice,
        prompt="x",
        variants_count=1,
        aspect_ratio="1:1",
        status=GenerationJob.Status.RUNNING,
    )
    resp = alice_api.get(reverse("ai:job-detail", kwargs={"pk": job.id}))
    assert resp.status_code == 200
    assert resp.json()["image_urls"] == []


def test_job_detail_404_for_other_user(
    alice_api: APIClient,
    bob: Any,
) -> None:
    job = GenerationJob.objects.create(
        user=bob,
        prompt="x",
        variants_count=1,
        aspect_ratio="1:1",
        status=GenerationJob.Status.READY,
    )
    resp = alice_api.get(reverse("ai:job-detail", kwargs={"pk": job.id}))
    assert resp.status_code == 404


def test_job_detail_requires_auth(api: APIClient, alice: Any) -> None:
    job = GenerationJob.objects.create(
        user=alice,
        prompt="x",
        variants_count=1,
        aspect_ratio="1:1",
    )
    resp = api.get(reverse("ai:job-detail", kwargs={"pk": job.id}))
    assert resp.status_code == 401


# ======================================================================
# Failure path through the Celery task
# ======================================================================


def test_lambda_failure_marks_job_failed(
    alice_api: APIClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _BoomLambda:
        def invoke(self, **kwargs: Any) -> dict[str, Any]:
            body = json.dumps({"errorMessage": "Bedrock content filter tripped"}).encode()
            return {"FunctionError": "Unhandled", "Payload": BytesIO(body)}

    monkeypatch.setattr(tasks.boto3, "client", lambda *a, **k: _BoomLambda())

    resp = alice_api.post(
        reverse("ai:generate"),
        data={"prompt": "x", "variants_count": 1, "aspect_ratio": "1:1"},
        format="json",
    )
    assert resp.status_code == 202
    job = GenerationJob.objects.get(pk=resp.json()["job_id"])
    assert job.status == GenerationJob.Status.FAILED
    assert "Bedrock content filter" in job.error
