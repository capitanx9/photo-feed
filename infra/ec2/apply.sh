#!/usr/bin/env bash
# Apply the production stack on EC2.
#
# Idempotent. Source of truth is main on github.com:
#   - infra/prod/images.env  → tags to deploy
#   - docker-compose.prod.yml → service definitions
#   - infra/nginx/*.conf     → nginx config
#
# Steps:
#   1. git pull → host matches main exactly (any local drift is dropped)
#   2. refresh .env from SSM (secrets only)
#   3. ECR login + docker pull (only the images that changed)
#   4. compose up -d (services with unchanged digests stay running)
#   5. migrations (idempotent — no-op if nothing pending)
#   6. health-check
#
# Rollback: `git revert <bad-commit>` on main → main has the bad tags
# replaced with the previous good ones → deploy-prod fires → host reverts.

set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/srv/photo-feed}"
AWS_REGION="${AWS_REGION:-eu-central-1}"
SSM_PREFIX="${SSM_PREFIX:-/photo-feed/prod}"
ECR_REGISTRY="${ECR_REGISTRY:-797890596022.dkr.ecr.eu-central-1.amazonaws.com}"
HEALTH_API="${HEALTH_API:-https://photo-feed.gotdns.ch/api/health/}"
HEALTH_WEB="${HEALTH_WEB:-https://photo-feed.gotdns.ch/en}"

cd "${PROJECT_DIR}"

# ----------------------------------------------------------------------
# 1. Self-sync from main. main is the contract; the host follows.
# ----------------------------------------------------------------------
git fetch origin main
git reset --hard origin/main

# ----------------------------------------------------------------------
# 2. Refresh runtime secrets in .env. images.env is the *tag* source;
#    .env is the *secrets* source. Disjoint sets, never collide.
# ----------------------------------------------------------------------
ssm_get() {
    aws ssm get-parameter \
        --name "${SSM_PREFIX}/$1" \
        --with-decryption \
        --region "${AWS_REGION}" \
        --query Parameter.Value \
        --output text
}

umask 077
{
    echo "DJANGO_SECRET_KEY=$(ssm_get DJANGO_SECRET_KEY)"
    echo "POSTGRES_PASSWORD=$(ssm_get POSTGRES_PASSWORD)"
    echo "WEBHOOK_SHARED_SECRET=$(ssm_get WEBHOOK_SHARED_SECRET)"
} > .env.new
mv .env.new .env

# ----------------------------------------------------------------------
# 3. Log in to ECR. Compose itself will pull only the digests it needs.
# ----------------------------------------------------------------------
aws ecr get-login-password --region "${AWS_REGION}" \
    | docker login --username AWS --password-stdin "${ECR_REGISTRY}"

# ----------------------------------------------------------------------
# 4. Bring the stack up. `--env-file` order matters:
#    - .env (default) — secrets
#    - infra/prod/images.env — versioned tags
#    Compose merges them in order; tags from images.env always win for
#    the variables defined there.
# ----------------------------------------------------------------------
COMPOSE="docker compose --env-file .env --env-file infra/prod/images.env -f docker-compose.prod.yml"
$COMPOSE pull
$COMPOSE up -d --remove-orphans

# ----------------------------------------------------------------------
# 5. Migrations. exec into the running web container so we don't need a
#    separate one-off image; safe to re-run because Django's migrate is
#    a no-op when nothing's pending.
# ----------------------------------------------------------------------
$COMPOSE exec -T web python manage.py migrate --noinput

# ----------------------------------------------------------------------
# 6. Health checks. Both halves must respond before we call this a win.
# ----------------------------------------------------------------------
smoke() {
    local url="$1"
    for attempt in 1 2 3 4 5; do
        status=$(curl -sk -o /dev/null -w '%{http_code}' "$url" || true)
        if [ "$status" = "200" ]; then
            echo "smoke: $url -> 200 OK"
            return 0
        fi
        echo "smoke attempt $attempt: $url -> $status, retrying..."
        sleep $((attempt * 2))
    done
    echo "smoke FAILED: $url did not return 200" >&2
    return 1
}

smoke "$HEALTH_API" || { $COMPOSE logs --tail 50 web      >&2; exit 1; }
smoke "$HEALTH_WEB" || { $COMPOSE logs --tail 50 web-front >&2; exit 1; }

echo "apply: ok"
