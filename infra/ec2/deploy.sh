#!/usr/bin/env bash
# Runs on the EC2 host (executed by SSM SendCommand from the cd-api
# workflow). Pulls SSM parameters into .env, pulls the new web image
# from ECR, restarts the web service, and runs migrations.
#
# Assumes (set up by infra/ec2-setup.md):
#   - /srv/photo-feed/docker-compose.prod.yml exists.
#   - /srv/photo-feed/infra/nginx/photo-feed.conf exists.
#   - The EC2 instance profile lets us read SSM parameters and
#     pull from ECR.
#   - nginx + certbot + postgres + redis are already running from a
#     previous compose-up; we only restart `web`.

set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/srv/photo-feed}"
AWS_REGION="${AWS_REGION:-eu-central-1}"
SSM_PREFIX="${SSM_PREFIX:-/photo-feed/prod}"
ECR_REGISTRY="${ECR_REGISTRY:?ECR_REGISTRY must be set, e.g. 797890596022.dkr.ecr.eu-central-1.amazonaws.com}"
ECR_REPO="${ECR_REPO:-photo-feed-api}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
HEALTH_URL="${HEALTH_URL:-https://photo-feed.gotdns.ch/api/health/}"

cd "${PROJECT_DIR}"

# ----------------------------------------------------------------------
# 1. Refresh .env from SSM (atomically — write to .env.new, then rename)
# ----------------------------------------------------------------------
ssm_get() {
    aws ssm get-parameter \
        --name "${SSM_PREFIX}/$1" \
        --with-decryption \
        --region "${AWS_REGION}" \
        --query Parameter.Value \
        --output text
}

IMAGE_URI="${ECR_REGISTRY}/${ECR_REPO}:${IMAGE_TAG}"

# IMAGE_URI must live in .env (not just shell env) — compose re-reads
# .env from disk on every restart, and without it `image: ${IMAGE_URI}`
# expands to empty and the web service fails to start.
umask 077
{
    echo "IMAGE_URI=${IMAGE_URI}"
    echo "DJANGO_SECRET_KEY=$(ssm_get DJANGO_SECRET_KEY)"
    echo "POSTGRES_PASSWORD=$(ssm_get POSTGRES_PASSWORD)"
    echo "WEBHOOK_SHARED_SECRET=$(ssm_get WEBHOOK_SHARED_SECRET)"
} > .env.new
mv .env.new .env

# ----------------------------------------------------------------------
# 2. Log in to ECR, pull the new image
# ----------------------------------------------------------------------
aws ecr get-login-password --region "${AWS_REGION}" \
    | docker login --username AWS --password-stdin "${ECR_REGISTRY}"

docker pull "${IMAGE_URI}"

# ----------------------------------------------------------------------
# 3. Bring up / restart the stack
# ----------------------------------------------------------------------
# `up -d` is idempotent — services that haven't changed stay running;
# `web` gets re-created with the new image because IMAGE_URI changed.
docker compose -f docker-compose.prod.yml up -d --remove-orphans

# ----------------------------------------------------------------------
# 4. Migrations
# ----------------------------------------------------------------------
docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput

# ----------------------------------------------------------------------
# 5. Smoke test
# ----------------------------------------------------------------------
# Curl 5 times with backoff in case nginx hasn't picked up the new
# upstream yet.
for attempt in 1 2 3 4 5; do
    status=$(curl -sk -o /dev/null -w '%{http_code}' "${HEALTH_URL}" || true)
    if [ "${status}" = "200" ]; then
        echo "smoke: ${HEALTH_URL} -> 200 OK"
        exit 0
    fi
    echo "smoke attempt ${attempt}: status=${status}, retrying..."
    sleep $((attempt * 2))
done

echo "smoke FAILED: ${HEALTH_URL} did not return 200" >&2
docker compose -f docker-compose.prod.yml logs --tail 50 web >&2
exit 1
