#!/usr/bin/env bash
# Sibling of deploy.sh — handles the Next.js web-front service.
# Invoked by the cd-web workflow via SSM SendCommand.
#
# Differences vs deploy.sh:
#   - Pushes a different env key (WEB_IMAGE_URI vs API_IMAGE_URI)
#   - Only restarts web-front; no migrations to run.
#   - Smoke-tests the public root URL instead of /api/health/.

set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/srv/photo-feed}"
AWS_REGION="${AWS_REGION:-eu-central-1}"
ECR_REGISTRY="${ECR_REGISTRY:?ECR_REGISTRY must be set, e.g. 797890596022.dkr.ecr.eu-central-1.amazonaws.com}"
ECR_REPO="${ECR_REPO:-photo-feed-web}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
HEALTH_URL="${HEALTH_URL:-https://photo-feed.gotdns.ch/en}"

cd "${PROJECT_DIR}"

# Self-sync from main: pull the latest infra files (this script,
# docker-compose.prod.yml, nginx config, sibling deploy.sh) so the host
# never drifts. See the longer comment in deploy.sh.
git fetch origin main
git reset --hard origin/main

WEB_IMAGE_URI="${ECR_REGISTRY}/${ECR_REPO}:${IMAGE_TAG}"

# Preserve the other service's image URI and the API secrets — we only
# rewrite the WEB_IMAGE_URI line.
if [ -f .env ]; then
    grep -v -E '^WEB_IMAGE_URI=' .env > .env.new || true
else
    : > .env.new
fi
echo "WEB_IMAGE_URI=${WEB_IMAGE_URI}" >> .env.new

umask 077
mv .env.new .env

# Log in to ECR, pull the new image.
aws ecr get-login-password --region "${AWS_REGION}" \
    | docker login --username AWS --password-stdin "${ECR_REGISTRY}"

docker pull "${WEB_IMAGE_URI}"

# `up -d` re-creates only the services whose image changed.
docker compose -f docker-compose.prod.yml up -d --remove-orphans

# Smoke test the root URL (nginx → next). Even an unauthenticated GET
# should return 200 (the feed page renders, just empty/login-prompt).
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
docker compose -f docker-compose.prod.yml logs --tail 50 web-front >&2
exit 1
