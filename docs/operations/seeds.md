# Demo data

`make seed-all` populates the database with a deterministic set of users,
posts, and orders so a fresh clone gets a usable demo state.

## Quick start

```bash
make up           # starts postgres + redis + django + mailhog
make migrate      # applies migrations
make seed-all     # creates 10 users, 50 posts, ~3 orders
```

Then log in via Bruno (`bruno/photo-feed/auth/login.bru`) or the frontend
with:

- **email:** `kyrylo@photo-feed.local`
- **password:** `pass1234`

## What gets created

| Command         | Effect |
|-----------------|--------|
| `seed_users`    | 10 users, emails `<handle>@photo-feed.local`, password `pass1234` |
| `seed_posts`    | 5 posts per demo user (mix of priced / unpriced) with `PostMedia.status='ready'` and placeholder S3 keys |
| `seed_orders`   | A handful of orders between demo users (alice→bob, bob→carol, dave→kyrylo) |
| `seed_all`      | Runs the three above in order |
| `flush_demo`    | Deletes every `@photo-feed.local` user (CASCADE removes their data) |

All seed commands are **idempotent** — re-running `seed_all` on a populated
DB is a no-op.

## Wipe and reseed

```bash
make reset-demo   # flush_demo + seed_all in one step
```

## Scoping by email domain

`flush_demo` deletes **only** users whose email ends in
`@photo-feed.local` (controlled by `settings.DEMO_USER_DOMAIN`). Any real
user — yourself, a teammate testing register, an integration-test
account — survives the flush. This is the only safety boundary; never
add a real user to the demo domain by mistake.

## Why placeholder S3 keys (no real files)

`seed_posts` writes `s3_key_raw` / `s3_key_resized` strings into
`PostMedia` rows but does **not** put any bytes into S3. The seed
command stays offline — it works on a fresh clone without AWS
credentials, without `localstack`, without internet.

The frontend handles missing media on its own (skeleton/placeholder
boxes). The full upload flow is exercised by the `posts` tests and by
real uploads through `/api/posts/upload-url/`.

## Order of dependencies (if you run commands separately)

```
seed_users  →  seed_posts  →  seed_orders
```

Running `seed_posts` before `seed_users` is a no-op with a warning;
running `seed_orders` before `seed_posts` skips because no priced posts
exist yet.
