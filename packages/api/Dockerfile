# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Manifests first — keep this layer cacheable across code changes.
COPY pyproject.toml uv.lock ./
COPY packages/api/pyproject.toml packages/api/pyproject.toml
COPY packages/cut_image/pyproject.toml packages/cut_image/pyproject.toml
COPY packages/generate_image/pyproject.toml packages/generate_image/pyproject.toml

RUN uv sync --frozen --no-install-project --package api

# Now the api package source.
COPY packages/api ./packages/api

RUN uv sync --frozen --package api

WORKDIR /app/packages/api

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
