"""Create the demo user pool. Idempotent."""

from common.seed_data import DEMO_DOMAIN, DEMO_PASSWORD, DEMO_USERS
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Create demo users (idempotent). Emails use the @photo-feed.local domain."

    def handle(self, *args: object, **options: object) -> None:
        created = 0
        for handle in DEMO_USERS:
            email = f"{handle}@{DEMO_DOMAIN}"
            user, was_created = User.objects.get_or_create(email=email)
            if was_created:
                user.set_password(DEMO_PASSWORD)
                user.save(update_fields=["password"])
                created += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"seed_users: {created} created, {len(DEMO_USERS) - created} already existed."
            )
        )
