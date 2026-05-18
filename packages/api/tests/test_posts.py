from typing import Any

import boto3
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from moto import mock_aws
from posts.models import Post, PostMedia
from rest_framework.test import APIClient

User = get_user_model()

PASSWORD = "sup3rsecret!"  # pragma: allowlist secret


# ======================================================================
# Fixtures
# ======================================================================

# === api client + auth ===


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


# === moto S3 bucket ===


@pytest.fixture
def s3_bucket():  # type: ignore[no-untyped-def]
    with mock_aws():
        client = boto3.client("s3", region_name=settings.AWS_REGION)
        client.create_bucket(
            Bucket=settings.S3_UPLOADS_BUCKET,
            CreateBucketConfiguration={"LocationConstraint": settings.AWS_REGION},
        )
        yield client


# ======================================================================
# Upload URL
# ======================================================================


@pytest.mark.django_db
def test_upload_url_creates_pending_media_and_returns_presign(
    alice_api: APIClient, s3_bucket: Any, alice: Any
) -> None:
    resp = alice_api.post(
        reverse("upload-url"),
        data={"content_type": "image/jpeg", "content_length": 12345, "kind": "post"},
        format="json",
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "upload_url" in body
    assert body["expires_in"] == settings.S3_PRESIGN_TTL_SECONDS
    assert body["s3_key"].startswith("raw/posts/")
    media = PostMedia.objects.get(pk=body["media_id"])
    assert media.owner_id == alice.id
    assert media.status == PostMedia.Status.PENDING


@pytest.mark.django_db
def test_upload_url_requires_auth(api: APIClient) -> None:
    resp = api.post(
        reverse("upload-url"),
        data={"content_type": "image/jpeg", "content_length": 1000},
        format="json",
    )
    assert resp.status_code == 401


@pytest.mark.django_db
def test_upload_url_rejects_disallowed_mime(alice_api: APIClient, s3_bucket: Any) -> None:
    resp = alice_api.post(
        reverse("upload-url"),
        data={"content_type": "application/x-msdownload", "content_length": 100},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_upload_url_rejects_oversize(alice_api: APIClient, s3_bucket: Any) -> None:
    too_big = settings.UPLOAD_MAX_BYTES + 1
    resp = alice_api.post(
        reverse("upload-url"),
        data={"content_type": "image/jpeg", "content_length": too_big},
        format="json",
    )
    assert resp.status_code == 400


# ======================================================================
# Media polling
# ======================================================================


@pytest.mark.django_db
def test_media_detail_returns_own_status(alice_api: APIClient, s3_bucket: Any, alice: Any) -> None:
    media = PostMedia.objects.create(owner=alice, s3_key_raw="raw/posts/1/x.jpg")
    resp = alice_api.get(reverse("media-detail", args=[media.id]))
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"


@pytest.mark.django_db
def test_media_detail_hides_others_media(alice_api: APIClient, s3_bucket: Any, bob: Any) -> None:
    media = PostMedia.objects.create(owner=bob, s3_key_raw="raw/posts/2/y.jpg")
    resp = alice_api.get(reverse("media-detail", args=[media.id]))
    assert resp.status_code == 404


# ======================================================================
# Lambda webhook
# ======================================================================


@pytest.mark.django_db
def test_webhook_marks_media_ready_with_valid_token(api: APIClient, alice: Any) -> None:
    media = PostMedia.objects.create(owner=alice, s3_key_raw="raw/posts/1/x.jpg")
    resp = api.post(
        reverse("internal:media-processed"),
        data={
            "s3_key": "raw/posts/1/x.jpg",
            "s3_key_resized": "resized/posts/1/x.jpg",
            "status": "ready",
        },
        format="json",
        HTTP_X_LAMBDA_TOKEN=settings.WEBHOOK_SHARED_SECRET,
    )
    assert resp.status_code == 204
    media.refresh_from_db()
    assert media.status == PostMedia.Status.READY
    assert media.s3_key_resized == "resized/posts/1/x.jpg"


@pytest.mark.django_db
def test_webhook_rejects_wrong_token(api: APIClient, alice: Any) -> None:
    media = PostMedia.objects.create(owner=alice, s3_key_raw="raw/posts/1/x.jpg")
    resp = api.post(
        reverse("internal:media-processed"),
        data={
            "s3_key": "raw/posts/1/x.jpg",
            "s3_key_resized": "resized/posts/1/x.jpg",
            "status": "ready",
        },
        format="json",
        HTTP_X_LAMBDA_TOKEN="wrong-token",  # pragma: allowlist secret
    )
    assert resp.status_code == 401
    media.refresh_from_db()
    assert media.status == PostMedia.Status.PENDING


@pytest.mark.django_db
def test_webhook_404_for_unknown_key(api: APIClient) -> None:
    resp = api.post(
        reverse("internal:media-processed"),
        data={
            "s3_key": "raw/posts/999/unknown.jpg",
            "s3_key_resized": "resized/posts/999/unknown.jpg",
            "status": "ready",
        },
        format="json",
        HTTP_X_LAMBDA_TOKEN=settings.WEBHOOK_SHARED_SECRET,
    )
    assert resp.status_code == 404


# ======================================================================
# Posts CRUD
# ======================================================================


@pytest.mark.django_db
def test_create_post_links_media(alice_api: APIClient, alice: Any) -> None:
    media = PostMedia.objects.create(
        owner=alice,
        s3_key_raw="raw/posts/1/x.jpg",
        s3_key_resized="resized/posts/1/x.jpg",
        status=PostMedia.Status.READY,
    )
    resp = alice_api.post(
        reverse("post-list"),
        data={"caption": "hello", "price": "9.99", "media_ids": [media.id]},
        format="json",
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["caption"] == "hello"
    assert body["owner_id"] == alice.id
    media.refresh_from_db()
    assert media.post_id == body["id"]


@pytest.mark.django_db
def test_create_post_rejects_someone_elses_media(alice_api: APIClient, bob: Any) -> None:
    media = PostMedia.objects.create(
        owner=bob, s3_key_raw="raw/posts/2/y.jpg", status=PostMedia.Status.READY
    )
    resp = alice_api.post(
        reverse("post-list"),
        data={"caption": "x", "media_ids": [media.id]},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_post_list_is_public(api: APIClient, alice: Any) -> None:
    Post.objects.create(owner=alice, caption="hello")
    resp = api.get(reverse("post-list"))
    assert resp.status_code == 200
    assert len(resp.json()["results"]) == 1


@pytest.mark.django_db
def test_post_detail_is_public(api: APIClient, alice: Any) -> None:
    post = Post.objects.create(owner=alice, caption="hello")
    resp = api.get(reverse("post-detail", args=[post.id]))
    assert resp.status_code == 200
    assert resp.json()["id"] == post.id


@pytest.mark.django_db
def test_post_update_requires_owner(alice_api: APIClient, bob: Any) -> None:
    post = Post.objects.create(owner=bob, caption="bob's")
    resp = alice_api.patch(
        reverse("post-detail", args=[post.id]),
        data={"caption": "stolen"},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_post_delete_by_owner(alice_api: APIClient, alice: Any) -> None:
    post = Post.objects.create(owner=alice, caption="bye")
    resp = alice_api.delete(reverse("post-detail", args=[post.id]))
    assert resp.status_code == 204
    assert not Post.objects.filter(pk=post.id).exists()


# ======================================================================
# Public user endpoints
# ======================================================================


@pytest.mark.django_db
def test_public_user_returns_id_and_email(api: APIClient, alice: Any) -> None:
    resp = api.get(reverse("users:user-detail", args=[alice.id]))
    assert resp.status_code == 200
    assert resp.json() == {"id": alice.id, "email": alice.email}


@pytest.mark.django_db
def test_public_user_posts(api: APIClient, alice: Any, bob: Any) -> None:
    Post.objects.create(owner=alice, caption="a1")
    Post.objects.create(owner=alice, caption="a2")
    Post.objects.create(owner=bob, caption="b1")
    resp = api.get(reverse("users:user-posts", args=[alice.id]))
    assert resp.status_code == 200
    captions = {p["caption"] for p in resp.json()["results"]}
    assert captions == {"a1", "a2"}


@pytest.mark.django_db
def test_patch_me_updates_email(alice_api: APIClient, alice: Any) -> None:
    resp = alice_api.patch(
        reverse("auth:me"),
        data={"email": "alice2@example.com"},
        format="json",
    )
    assert resp.status_code == 200
    alice.refresh_from_db()
    assert alice.email == "alice2@example.com"
