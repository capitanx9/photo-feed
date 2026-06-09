"""Seed each demo user with a fixed set of posts. Idempotent.

Generates a real placeholder PNG per post via Pillow and uploads it to the
configured S3 bucket (MinIO in dev) under the same key recorded in PostMedia.
This way the feed renders actual images — no try/except around presign,
no broken thumbnails in the UI.
"""

import io
import uuid
from decimal import Decimal

from common.s3 import get_s3_client
from common.seed_data import DEMO_CAPTIONS, DEMO_DOMAIN, DEMO_PRICES, POSTS_PER_USER
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw

from posts.models import Post, PostMedia

User = get_user_model()

# Deterministic colour palette so the same handle always gets the same picture.
PALETTE = [
    (231, 76, 60),  # red
    (52, 152, 219),  # blue
    (46, 204, 113),  # green
    (241, 196, 15),  # yellow
    (155, 89, 182),  # purple
    (230, 126, 34),  # orange
    (26, 188, 156),  # teal
    (52, 73, 94),  # slate
    (236, 240, 241),  # light grey
    (149, 165, 166),  # grey
]

IMAGE_SIZE = (1080, 1080)


def _render_placeholder(label: str, color_seed: int) -> bytes:
    """Return JPEG bytes — a solid-coloured 1080x1080 square with the label centred."""
    color = PALETTE[color_seed % len(PALETTE)]
    img = Image.new("RGB", IMAGE_SIZE, color=color)
    draw = ImageDraw.Draw(img)
    text_color = (255, 255, 255) if sum(color) < 380 else (40, 40, 40)
    # PIL default font is tiny — anchor centred so the label is at least visible.
    draw.text((IMAGE_SIZE[0] // 2, IMAGE_SIZE[1] // 2), label, fill=text_color, anchor="mm")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True)
    return buf.getvalue()


class Command(BaseCommand):
    help = (
        "Create demo posts (and their PostMedia rows) for each demo user. "
        "Generates a placeholder JPEG per post and uploads it to S3 so the "
        "feed shows real images. Idempotent."
    )

    def handle(self, *args: object, **options: object) -> None:
        demo_users = User.objects.filter(email__iendswith=f"@{DEMO_DOMAIN}")
        if not demo_users.exists():
            self.stdout.write(
                self.style.WARNING("seed_posts: no demo users found. Run seed_users first.")
            )
            return

        s3 = get_s3_client()
        created_posts = 0
        skipped_users = 0
        for user_index, user in enumerate(demo_users):
            if user.posts.count() >= POSTS_PER_USER:
                skipped_users += 1
                continue
            for i in range(POSTS_PER_USER):
                price_str = DEMO_PRICES[i % len(DEMO_PRICES)]
                price = Decimal(price_str) if price_str is not None else None
                caption = DEMO_CAPTIONS[i % len(DEMO_CAPTIONS)]
                post = Post.objects.create(
                    owner=user,
                    caption=caption,
                    price=price,
                    status=Post.Status.PUBLISHED,
                )
                media_uuid = uuid.uuid4().hex
                resized_key = f"resized/posts/{user.id}/{media_uuid}.jpg"
                raw_key = f"raw/posts/{user.id}/{media_uuid}.jpg"
                # In prod cut_image Lambda fills resized/ from raw/; in seed we
                # skip the round-trip and write resized/ directly.
                png_bytes = _render_placeholder(
                    f"{user.email.split('@')[0]}\npost #{i + 1}",
                    color_seed=user_index * POSTS_PER_USER + i,
                )
                s3.put_object(
                    Bucket=settings.S3_UPLOADS_BUCKET,
                    Key=resized_key,
                    Body=png_bytes,
                    ContentType="image/jpeg",
                )
                PostMedia.objects.create(
                    post=post,
                    owner=user,
                    kind=PostMedia.Kind.POST,
                    s3_key_raw=raw_key,
                    s3_key_resized=resized_key,
                    status=PostMedia.Status.READY,
                )
                created_posts += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"seed_posts: {created_posts} posts created, "
                f"{skipped_users} users already had posts."
            )
        )
