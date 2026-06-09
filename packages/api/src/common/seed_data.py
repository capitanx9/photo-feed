"""Shared constants for the seed_* / reset_all management commands.

Kept separate so each command stays focused and tests can import the same
canonical lists without re-declaring them.
"""

DEMO_DOMAIN = "photo-feed.local"
DEMO_PASSWORD = "pass1234"  # noqa: S105  # pragma: allowlist secret

# Order matters — the first user is the one Bruno's collection variables
# point at, so demo logins always land on the same account.
DEMO_USERS = [
    "kyrylo",
    "alice",
    "bob",
    "carol",
    "dave",
    "eve",
    "frank",
    "grace",
    "heidi",
    "ivan",
]

POSTS_PER_USER = 5

DEMO_CAPTIONS = [
    "Sunset over the lake",
    "Espresso at the corner cafe",
    "New running shoes",
    "Weekend hike",
    "Studio shot — handmade mug",
]

# Some posts get a price (shoppable), some don't (just feed content) —
# mirrors how Instagram-shop posts look in production.
DEMO_PRICES = ["19.99", None, "9.50", None, "42.00"]
