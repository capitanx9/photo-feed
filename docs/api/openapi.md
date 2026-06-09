# OpenAPI

The OpenAPI 3 spec is the single source of truth for request /
response shapes. Generated from Django code by `drf-spectacular`.

## Where to fetch it

- **Live, from a running server:** `GET /api/schema/`
- **Checked-in file:** [`schemas/openapi.yaml`](../../schemas/openapi.yaml)

CI fails if the checked-in file disagrees with the code.

UIs in dev:

```bash
make up
make swagger-up                                  # opens Swagger UI
# Redoc is at http://localhost:8000/api/schema/redoc/
```

## Regenerate after backend changes

```bash
make gen-api                # writes schemas/openapi.yaml
git add schemas/openapi.yaml
```

CI runs `make gen-api-check` on every `packages/api/**` change;
if the file is stale, CI fails. Always regenerate **and commit** before
pushing.

## Generating a typed client

For TypeScript / React the smallest tool is `openapi-typescript`:

```bash
npx openapi-typescript https://photo-feed.gotdns.ch/api/schema/ \
    -o src/api/schema.ts
```

For richer code-gen (fetchers + hooks per operation), `orval` or
`openapi-fetch` both work — pick one. The spec is clean enough that
no manual fix-ups are needed.

For local dev, point at `http://localhost:8000/api/schema/` instead.

## Schema conventions

- **`operationId`** is auto-generated from URL + method
  (`posts_list`, `auth_login_create`). Client generators use it as
  the function name.
- **Tags** group operations by feature: `auth`, `users`, `posts`,
  `cart`, `orders`, `ai`, `health`. Scope generated client output to
  one slice via tags for a smaller bundle.
- **Pagination**: cursor-based. Response envelope is
  `{next, previous, results}`. The cursor is opaque — treat it as a
  string.
- **Errors**:
  - Single error: `{"detail": "string"}`
  - Validation error: `{"field_name": ["msg", ...]}`
- **Timestamps**: ISO-8601 UTC, e.g. `2026-06-09T12:34:56Z`.
- **IDs**: integers today; subject to change. Use the OpenAPI types.
