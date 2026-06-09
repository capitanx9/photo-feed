# Seeds

Before debugging anything, get the DB to a known state.

## Create

| Command | Effect |
|---|---|
| `make seed-users` | 10 users with emails `<handle>@photo-feed.local`, password `pass1234` |
| `make seed-posts` | 5 posts per user (mix of priced / unpriced), placeholder JPEG uploaded to the uploads bucket, `status='ready'` |
| `make seed-orders` | Sample orders between users (alice→bob, bob→carol, dave→kyrylo) |
| `make seed-all` | All three above in order |

All `seed-*` targets are idempotent — re-running on a populated DB
is a no-op.

If you run them separately, order matters:

```
make seed-users  →  make seed-posts  →  make seed-orders
```

`seed-posts` before `seed-users` is a no-op with a warning;
`seed-orders` before `seed-posts` skips because no priced posts
exist yet.

## Reset

```bash
make reset
```

Deletes **every** user (CASCADE removes their posts, media,
orders). Does not reseed — run `make seed-all` separately if you
want fresh data.

The standard "clean state for debugging" loop:

```bash
make reset
make seed-all
```

## A note on S3 (local vs prod)

`seed-posts` renders a placeholder JPEG per post via Pillow and
**uploads it to the uploads bucket** (`S3_UPLOADS_BUCKET`). The
generated objects land at
`resized/posts/<user_id>/<uuid>.jpg`. So the feed shows real
images, not broken thumbnails.

What that means in practice:

- **Local (MinIO):** the placeholder JPEGs go into the MinIO
  bucket created by `minio-init`. No AWS network involved.
- **Prod (real AWS S3):** if you run `seed-posts` on the EC2 box,
  the same JPEGs will be uploaded to the real `photo-feed-uploads`
  bucket — they'll live there until you delete them manually.
  Don't seed prod unless you genuinely want demo data + demo
  objects to appear in real S3.

The full real-user upload flow (presigned PUT + cut_image Lambda
trigger) goes through `POST /api/posts/upload-url/` — drive it
from the Bruno collection (see [`../api/bruno.md`](../api/bruno.md)),
not from seeds.
