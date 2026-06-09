# Local dev stack — how it's wired

Defined in [`docker-compose.dev.yml`](../../docker-compose.dev.yml).
`make up` brings it up; `make down` stops it.

## Services

| Service | Image | Host port | Purpose |
|---|---|---|---|
| `web` | built from `packages/api/Dockerfile` | `8000` | Django + DRF, `runserver` via `manage.py` |
| `db` | `postgres:16-alpine` | `5432` | Primary DB |
| `redis` | `redis:7-alpine` | `6379` | Cache + Celery broker |
| `mailhog` | `mailhog/mailhog:latest` | `1025` SMTP / `8025` UI | Captures outbound mail; UI at `http://localhost:8025` |
| `minio` | `minio/minio:latest` | `9000` API / `9001` console | S3-compatible local object store |
| `minio-init` | `minio/mc:latest` | — | One-shot: creates buckets, sets download policy |

`web` mounts source live:

```yaml
volumes:
  - ./packages/api/src:/app/packages/api/src
  - ./packages/api/manage.py:/app/packages/api/manage.py
```

Changes to Django code reload immediately via `runserver`. The
Dockerfile is shared with prod — only the runtime command differs.

## MinIO buckets

`minio-init` creates these on first start:

- `photo-feed-uploads`
- `photo-feed-generated-usw2`

Console: `http://localhost:9001` (login `minioadmin` / `minioadmin`).

The api talks to MinIO via two endpoints set in `packages/api/.env`:

```bash
AWS_S3_ENDPOINT_URL=http://minio:9000             # boto3 inside web container
AWS_S3_PUBLIC_ENDPOINT_URL=http://localhost:9000  # presigned URLs the browser will hit
```

The split matters: presigned URLs are signed against the **public**
hostname so the browser can use them. The api itself talks to MinIO
over the internal Docker network. If both used the same hostname,
one of the two would not resolve.

## Env file

`web` reads `packages/api/.env`. Bootstrap from the example:

```bash
cp packages/api/.env.example packages/api/.env
```

The example ships safe local defaults — demo password `pass1234`,
plaintext local secret key, etc. **Never** copy this file to prod;
prod reads from SSM Parameter Store via
[`prod-remote.md`](prod-remote.md).

## Common operations

All `make` — same surface in every page:

| Want to | Command |
|---|---|
| Up / down | `make up` / `make down` |
| Apply migrations | `make migrate` |
| Tail all logs | `make logs` |
| Tail one service | `make logs-web` / `make logs-db` / `make logs-redis` / `make logs-mailhog` |
| Django shell | `make shell` (uses `shell_plus`) |
| Web container shell | `make bash` |
| Seed demo data | `make seed-all` (see [`../debug/seeds.md`](../debug/seeds.md)) |
| Wipe everything | `make reset` |
| Regenerate OpenAPI | `make gen-api` |
| Swagger UI | `make swagger-up` |

## Hard reset (drops Postgres + MinIO data)

```bash
make down
docker volume rm \
  photo-feed_postgres_data \
  photo-feed_redis_data \
  photo-feed_minio_data
make up && make migrate && make seed-all
```

## Sanity

```bash
curl -s http://localhost:8000/api/health/
# {"ok":true}
```
