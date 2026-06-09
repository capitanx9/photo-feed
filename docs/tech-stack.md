# Tech stack

What this project is built from, and why each choice.

## Application

| Tech | Version | Why |
|---|---|---|
| **Python** | 3.12 | Modern type hints, `match`/`except*`, `tomllib`. Pinned via `.python-version`. |
| **Django** | 5.x | Mature ORM + admin + auth scaffolding. Pays for itself within a day. |
| **Django REST Framework** | latest | API serializers, viewsets, throttling — saves writing the same code by hand. |
| **drf-spectacular** | latest | Generates the OpenAPI 3 spec from DRF code. Frontend gets a typed contract for free. |
| **djangorestframework-simplejwt** | latest | JWT issuance / refresh. We layer cookie-based auth on top. |
| **psycopg (3.x)** | latest | The current Postgres driver. Replaces `psycopg2`. |
| **gunicorn** | 26.x | Battle-tested sync WSGI server. Three workers per t3.small are enough. |

## Async + background

| Tech | Why |
|---|---|
| **Celery** | The standard for "do this off the request thread" in Django. |
| **Redis 7** | Celery broker + result backend + Django cache. One service, three jobs. |

## Storage

| Tech | Why |
|---|---|
| **Postgres 16** | Default RDBMS. JSON columns when we need them, real transactions, mature migration story. |
| **AWS S3** | Two buckets: `photo-feed-uploads` (raw + resized) in eu-central-1, `photo-feed-generated-usw2` (AI output) in us-west-2. |
| **MinIO** | S3-compatible local server used in dev so the upload flow runs offline. |

## AI

| Tech | Why |
|---|---|
| **AWS Lambda — `cut_image`** | Triggered by S3 `ObjectCreated` on `raw/`. Pillow resize, no ML. |
| **AWS Lambda — `generate_image`** | Calls Bedrock. Lives in `us-west-2` because that's the only region where Bedrock Stability is ACTIVE. |
| **Amazon Bedrock — Stability AI** | `stability.stable-image-core-v1:1` (default), with `stable-image-ultra-v1:1` and `sd3-5-large-v1:0` reachable via an env var. |

## Infra & runtime

| Tech | Why |
|---|---|
| **Docker + Docker Compose** | One toolchain for dev and prod. `docker-compose.dev.yml` vs `docker-compose.prod.yml`. |
| **nginx 1.27 (alpine)** | TLS termination, HTTP→HTTPS redirect, reverse proxy to gunicorn. |
| **Let's Encrypt + certbot** | Free TLS, auto-renewal via a sidecar container. |
| **AWS EC2 (Ubuntu 24.04, t3.small/medium)** | Single instance running the prod compose stack. |
| **AWS ECR** | Private registry for the api image. Pulled by `deploy.sh`. |
| **AWS SAM** | Defines + deploys the two Lambdas via CloudFormation. |
| **AWS Systems Manager (SSM)** | Two roles: agent for keyless deploy (`SendCommand`), Parameter Store for runtime secrets. |
| **AWS IAM + OIDC** | GitHub Actions federate into deployer roles. No long-lived AWS keys anywhere. |

## Tooling (dev experience)

| Tech | Why |
|---|---|
| **uv** | Resolves and locks Python deps faster than pip + pip-tools combined. Workspaces support our multi-package layout. |
| **ruff** | Lint and format in one tool. Replaces flake8 + black + isort + pyupgrade. |
| **mypy** | Static type checking on the api package. |
| **pytest** | Test runner for api and lambdas. `pytest-django` for the Django pieces. |
| **moto** | Mocks boto3 calls in tests so no AWS network is needed. |
| **pre-commit** | Runs ruff, hooks, and a custom `commit-msg` check on every commit. |
| **make** | Single command surface for every routine task. See the Makefile and `makefiles/*.mk`. |
| **Bruno** | Versioned API request collection in `bruno/photo-feed/`. The team's alternative to Postman/Swagger. |

## CI / CD

| Tech | Why |
|---|---|
| **GitHub Actions** | CI (`ci-api`, `ci-lambdas`) and CD (`cd-api`, `cd-lambdas`). |
| **OIDC into AWS** | Each workflow assumes a scoped deployer role with short-lived STS credentials. |
| **CloudFormation** | Used implicitly via SAM — the two app stacks plus a SAM-managed artifact stack per region. |
