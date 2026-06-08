"""Delete every user whose email belongs to the demo domain. CASCADE handles the rest."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from orders.models import Order

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Delete all demo users (email ending in @photo-feed.local). "
        "CASCADE removes their posts, media, cart, generation jobs. "
        "Orders are explicitly deleted first because OrderItem.post is PROTECT — "
        "that's the right behaviour in prod (don't lose history of sold posts), but "
        "for demo data we want a clean wipe."
    )

    def handle(self, *args: object, **options: object) -> None:
        demo_users = User.objects.filter(email__iendswith=f"@{settings.DEMO_USER_DOMAIN}")
        with transaction.atomic():
            # Drop orders by demo buyers AND orders that reference posts owned by demo
            # users (a real-user-buying-from-demo-seller case can't exist in seed data
            # but we cover it defensively).
            Order.objects.filter(user__in=demo_users).delete()
            Order.objects.filter(items__post__owner__in=demo_users).distinct().delete()
            count = demo_users.count()
            demo_users.delete()
        self.stdout.write(self.style.SUCCESS(f"flush_demo: removed {count} demo users."))
