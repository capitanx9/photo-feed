"""Seed each demo user with a fixed set of posts. Idempotent."""

import uuid
from decimal import Decimal

from common.seed_data import DEMO_CAPTIONS, DEMO_PRICES, POSTS_PER_USER
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from posts.models import Post, PostMedia

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Create demo posts (and their PostMedia rows) for each demo user. "
        "Idempotent: a user that already has demo posts is skipped."
    )

    def handle(self, *args: object, **options: object) -> None:
        demo_users = User.objects.filter(email__iendswith=f"@{settings.DEMO_USER_DOMAIN}")
        if not demo_users.exists():
            self.stdout.write(
                self.style.WARNING("seed_posts: no demo users found. Run seed_users first.")
            )
            return

        created_posts = 0
        skipped_users = 0
        for user in demo_users:
            if user.posts.count() >= POSTS_PER_USER:
                skipped_users += 1
                continue
            for i in range(POSTS_PER_USER):
                price_str = DEMO_PRICES[i % len(DEMO_PRICES)]
                price = Decimal(price_str) if price_str is not None else None
                post = Post.objects.create(
                    owner=user,
                    caption=DEMO_CAPTIONS[i % len(DEMO_CAPTIONS)],
                    price=price,
                    status=Post.Status.PUBLISHED,
                )
                media_uuid = uuid.uuid4().hex
                PostMedia.objects.create(
                    post=post,
                    owner=user,
                    kind=PostMedia.Kind.POST,
                    s3_key_raw=f"raw/posts/{user.id}/{media_uuid}.jpg",
                    s3_key_resized=f"resized/posts/{user.id}/{media_uuid}.jpg",
                    status=PostMedia.Status.READY,
                )
                created_posts += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"seed_posts: {created_posts} posts created, "
                f"{skipped_users} users already had posts."
            )
        )
