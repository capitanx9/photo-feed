import boto3
import pytest
from common.seed_data import DEMO_DOMAIN, DEMO_PASSWORD, DEMO_USERS, POSTS_PER_USER
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from moto import mock_aws
from orders.models import Order
from posts.models import Post, PostMedia

User = get_user_model()


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _s3_bucket():
    """seed_posts now writes a real PNG to S3 per post — provide a moto-backed
    bucket so the command runs against an in-memory S3 in tests."""
    with mock_aws():
        boto3.client("s3", region_name=settings.AWS_REGION).create_bucket(
            Bucket=settings.S3_UPLOADS_BUCKET,
            CreateBucketConfiguration={"LocationConstraint": settings.AWS_REGION},
        )
        yield


# ======================================================================
# seed_users
# ======================================================================


def test_seed_users_creates_all_demo_users() -> None:
    call_command("seed_users")
    emails = set(
        User.objects.filter(email__iendswith=f"@{DEMO_DOMAIN}").values_list(
            "email", flat=True
        )
    )
    assert emails == {f"{h}@{DEMO_DOMAIN}" for h in DEMO_USERS}


def test_seed_users_is_idempotent() -> None:
    call_command("seed_users")
    first = User.objects.count()
    call_command("seed_users")
    assert User.objects.count() == first


def test_seed_users_sets_login_password() -> None:
    call_command("seed_users")
    kyrylo = User.objects.get(email=f"kyrylo@{DEMO_DOMAIN}")
    assert kyrylo.check_password(DEMO_PASSWORD)


# ======================================================================
# seed_posts
# ======================================================================


def test_seed_posts_creates_n_posts_per_demo_user() -> None:
    call_command("seed_users")
    call_command("seed_posts")
    for handle in DEMO_USERS:
        user = User.objects.get(email=f"{handle}@{DEMO_DOMAIN}")
        assert user.posts.count() == POSTS_PER_USER
        # every post has its PostMedia row, ready, with both keys populated
        for post in user.posts.all():
            media = post.media.get()
            assert media.status == PostMedia.Status.READY
            assert media.s3_key_raw.startswith(f"raw/posts/{user.id}/")
            assert media.s3_key_resized.startswith(f"resized/posts/{user.id}/")


def test_seed_posts_is_idempotent() -> None:
    call_command("seed_users")
    call_command("seed_posts")
    first = Post.objects.count()
    call_command("seed_posts")
    assert Post.objects.count() == first


def test_seed_posts_no_op_without_users(capsys: pytest.CaptureFixture[str]) -> None:
    call_command("seed_posts")
    assert Post.objects.count() == 0
    out = capsys.readouterr().out
    assert "no demo users" in out.lower()


# ======================================================================
# seed_orders
# ======================================================================


def test_seed_orders_creates_orders_between_demo_users() -> None:
    call_command("seed_users")
    call_command("seed_posts")
    call_command("seed_orders")
    assert Order.objects.count() >= 1
    for order in Order.objects.all():
        assert order.user.email.endswith(f"@{DEMO_DOMAIN}")
        assert order.total > 0
        assert order.items.count() >= 1


def test_seed_orders_is_idempotent() -> None:
    call_command("seed_users")
    call_command("seed_posts")
    call_command("seed_orders")
    first = Order.objects.count()
    call_command("seed_orders")
    assert Order.objects.count() == first


# ======================================================================
# seed_all + reset_all
# ======================================================================


def test_seed_all_runs_full_chain() -> None:
    call_command("seed_all")
    assert User.objects.count() == len(DEMO_USERS)
    assert Post.objects.count() == len(DEMO_USERS) * POSTS_PER_USER
    assert Order.objects.count() >= 1


def test_reset_all_removes_every_user() -> None:
    """reset_all is intentionally unscoped — it wipes ALL users, not just demo
    ones. The seed-users-and-then-reset flow is the standard 'clean state for
    debugging' loop. There is no opt-out and no domain filter.
    """
    call_command("seed_all")
    # Add a non-demo user too; reset must remove this one as well.
    User.objects.create_user(
        email="alice@example.com",
        password="sup3rsecret!",  # pragma: allowlist secret
    )
    call_command("reset_all")
    assert User.objects.count() == 0
    assert Post.objects.count() == 0
    assert Order.objects.count() == 0
    assert PostMedia.objects.count() == 0


def test_reset_all_is_safe_on_empty_db() -> None:
    call_command("reset_all")
    assert User.objects.count() == 0
