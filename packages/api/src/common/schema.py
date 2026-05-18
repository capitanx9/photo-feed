"""Helpers that pin down a uniform shape for every @extend_schema usage."""

from typing import Any

from drf_spectacular.utils import OpenApiResponse, extend_schema

from .serializers import ErrorSerializer

# ======================================================================
# Reusable error responses
# ======================================================================

ERROR_400 = OpenApiResponse(response=ErrorSerializer, description="Validation error")
ERROR_401 = OpenApiResponse(response=ErrorSerializer, description="Authentication required")
ERROR_429 = OpenApiResponse(response=ErrorSerializer, description="Rate limit exceeded")


# ======================================================================
# Tag-bound decorators
# ======================================================================


def tagged_schema(
    tag: str,
    *,
    summary: str,
    description: str,
    request: Any = None,
    responses: dict[int, Any],
) -> Any:
    return extend_schema(
        tags=[tag],
        summary=summary,
        description=description,
        request=request,
        responses=responses,
    )


def auth_schema(**kwargs: Any) -> Any:
    return tagged_schema("auth", **kwargs)


def health_schema(**kwargs: Any) -> Any:
    return tagged_schema("health", **kwargs)
