"""Run seed_users → seed_posts → seed_orders in one go."""

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run all seed commands in dependency order."

    def handle(self, *args: object, **options: object) -> None:
        for name in ("seed_users", "seed_posts", "seed_orders"):
            self.stdout.write(self.style.NOTICE(f"-> {name}"))
            call_command(name)
