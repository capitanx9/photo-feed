.DEFAULT_GOAL := help

# --- Meta ---
include makefiles/vars.mk
include makefiles/help.mk
include makefiles/clean.mk

# --- Common (used by both halves) ---
include makefiles/common/docker-lifecycle.mk
include makefiles/common/docker-logs.mk
include makefiles/common/openapi.mk

# --- Back (Django + Lambdas) ---
include makefiles/back/docker-image.mk
include makefiles/back/django/db.mk
include makefiles/back/django/users.mk
include makefiles/back/data/seed.mk
include makefiles/back/quality/lint.mk
include makefiles/back/quality/test.mk
include makefiles/back/tooling-uv.mk
include makefiles/back/sam/build.mk
include makefiles/back/aws/bedrock-check.mk

# --- Front (Next.js) ---
include makefiles/front/lifecycle.mk
include makefiles/front/lint.mk
