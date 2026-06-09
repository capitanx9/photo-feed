"""Delete every user. CASCADE handles the rest."""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from orders.models import Order

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Delete all users. CASCADE removes their posts, media, cart, and "
        "generation jobs. Orders are explicitly deleted first because "
        "OrderItem.post is PROTECT — that's the right behaviour in prod "
        "(don't lose history of sold posts), but for a full reset we want "
        "a clean wipe."
    )

    def handle(self, *args: object, **options: object) -> None:
        with transaction.atomic():
            Order.objects.all().delete()
            count, _ = User.objects.all().delete()
        self.stdout.write(
            self.style.SUCCESS(f"reset_all: removed {count} users (and cascaded children).")
        )
