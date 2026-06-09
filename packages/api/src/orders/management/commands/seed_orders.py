"""Seed a few demo orders so the orders-history UI has something to render."""

from decimal import Decimal

from common.seed_data import DEMO_DOMAIN
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from orders.models import Order, OrderItem

User = get_user_model()


# (buyer_handle, seller_handle, qty_of_first_priced_post)
DEMO_ORDERS = [
    ("alice", "bob", 1),
    ("bob", "carol", 2),
    ("dave", "kyrylo", 1),
]

DEMO_SHIPPING = {
    "shipping_name": "Demo Buyer",
    "shipping_address": "1 Demo Street",
    "shipping_city": "Dublin",
    "shipping_zip": "D01 ABC1",
    "shipping_country": "IE",
}


class Command(BaseCommand):
    help = "Create a few sample orders between demo users (idempotent: skips users who already have orders)."

    def handle(self, *args: object, **options: object) -> None:
        created = 0
        for buyer_handle, seller_handle, qty in DEMO_ORDERS:
            buyer_email = f"{buyer_handle}@{DEMO_DOMAIN}"
            seller_email = f"{seller_handle}@{DEMO_DOMAIN}"
            try:
                buyer = User.objects.get(email=buyer_email)
                seller = User.objects.get(email=seller_email)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f"seed_orders: skipping {buyer_handle}→{seller_handle}: "
                        "run seed_users first."
                    )
                )
                continue

            if Order.objects.filter(user=buyer).exists():
                continue

            post = seller.posts.filter(price__isnull=False).first()
            if post is None:
                self.stdout.write(
                    self.style.WARNING(
                        f"seed_orders: {seller_handle} has no priced posts — skipping."
                    )
                )
                continue

            with transaction.atomic():
                order = Order.objects.create(
                    user=buyer,
                    status=Order.Status.PAID,
                    total=Decimal(post.price) * qty,
                    payment_method="card",
                    **DEMO_SHIPPING,
                )
                OrderItem.objects.create(
                    order=order,
                    post=post,
                    qty=qty,
                    price_at_purchase=post.price,
                )
            created += 1

        self.stdout.write(self.style.SUCCESS(f"seed_orders: {created} orders created."))
