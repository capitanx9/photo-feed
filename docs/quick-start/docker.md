# Quick start — local Docker stack

From clone to a working `/api/health/` in ~5 minutes.

## Prereqs (on macOS)

```bash
brew install --cask docker     # Docker Desktop (also installs `docker compose`)
brew install uv                # Python toolchain (manages Python + deps)
brew install make              # macOS ships an old GNU make; this gets a current one
brew install pre-commit        # commit hooks
```

Open Docker Desktop once after install so it has permission to run.

Verify:

```bash
docker --version
docker compose version
uv --version
make --version
```

## Clone and bring the stack up

```bash
git clone https://github.com/capitanx9/photo-feed.git
cd photo-feed

cp packages/api/.env.example packages/api/.env   # safe local defaults

make install     # uv sync --all-packages
make up          # postgres + redis + mailhog + minio + web
make migrate     # apply Django migrations
make seed-all    # demo users + posts + orders (see debug/seeds.md)
```

Smoke check:

```bash
curl -s http://localhost:8000/api/health/
# {"ok":true}
```

For driving the api, watching logs, resetting data — see
[`../debug/`](../debug/).

