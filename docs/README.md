# photo-feed docs

## What this project is

- [overview](overview.md) — what the application does, scope and non-goals (functional).
- [tech-stack](tech-stack.md) — what it's built from and why those choices.
- [architecture](architecture.md) — how the parts connect at runtime, identity model, region split.

## Quick start

- [quick-start/docker](quick-start/docker.md) — macOS prereqs + `make` commands to bring the local stack up.
- [quick-start/ec2](quick-start/ec2.md) — SSH into the running prod box; daily docker-compose ops there.

## Debug

- [debug/seeds](debug/seeds.md) — `make seed-*` / `make reset` for a deterministic data state.
- [debug/logs](debug/logs.md) — `make logs-*` locally and on EC2 (same targets after `ssh photo-feed`); CloudWatch for Lambdas.
- [debug/api-testing](debug/api-testing.md) — Bruno on one side, `make logs-web` on the other.

## Develop

- [develop/pre-commit](develop/pre-commit.md) — hooks that run on `git commit`, including the AI-coauthorship block.
- [develop/testing](develop/testing.md) — `make test`, `make test-lambdas`, `make check`.
- [develop/ci](develop/ci.md) — `ci-api` and `ci-lambdas` workflows: same `make` targets, no surprises.

## Deploy

- [deploy/dev-local](deploy/dev-local.md) — `docker-compose.dev.yml` services, MinIO, Mailhog, env file.
- [deploy/prod-remote](deploy/prod-remote.md) — full CD chain: OIDC, deployer roles, SSM, ECR, CloudFormation, EC2 bootstrap, failure modes.

## API (for the frontend)

- [api/auth](api/auth.md) — JWT-in-cookie flow, refresh, CSRF, CORS.
- [api/openapi](api/openapi.md) — where to fetch the schema, typed-client generation.
- [api/bruno](api/bruno.md) — install the Bruno desktop client and open the collection in `bruno/photo-feed/`.
