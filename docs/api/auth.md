# Auth

**Cookie-based JWT with refresh-token rotation.** Access + refresh
JWTs are issued by the backend and delivered as `HttpOnly` cookies —
the frontend never reads or stores the token in JavaScript, and
JS-based XSS can't exfiltrate it.

The frontend treats it as a session (just send requests with cookies
attached); under the hood it's two short-lived JWTs.

## Endpoints

| Method | Path | What |
|---|---|---|
| POST | `/api/auth/register/` | Create account (does not log in) |
| POST | `/api/auth/login/` | Set `access` + `refresh` cookies |
| POST | `/api/auth/refresh/` | Rotate `access` (reads refresh cookie) |
| POST | `/api/auth/logout/` | Clear both cookies |
| GET  | `/api/auth/me/` | Current user; 401 if not signed in |

All are rate-limited per IP. On `429`, back off until the
`Retry-After` time.

To actually fire these — request bodies, expected responses, the
whole flow — open the Bruno collection. See
[`bruno.md`](bruno.md).

## Cookie semantics

Two cookies are set on `/api/auth/login/`:

| Cookie | TTL | Flags |
|---|---|---|
| `access` | 5 min | `HttpOnly`, `Secure` (prod), `SameSite=Lax`, `Path=/api/` |
| `refresh` | 7 days | `HttpOnly`, `Secure` (prod), `SameSite=Lax`, `Path=/api/auth/refresh/` |

The `Path=/api/auth/refresh/` on the refresh cookie is intentional —
only the refresh endpoint can see it, so a `/api/posts/` request
can't accidentally include the long-lived token.

## Refresh-token rotation

```
login                                  → set access (5m) + refresh (7d)
api call                               → access cookie attached
access expires → 401 → refresh         → new access cookie, retry
refresh expires → 401 on refresh       → force re-login
logout                                 → both cookies cleared
```

Each `POST /api/auth/refresh/` issues a **new** access cookie. The
refresh cookie itself is also rotated on every use, so a stolen
refresh token can only be used once before the legitimate user's
next refresh invalidates it.

## CSRF

Django CSRF is **disabled** for JSON endpoints under `/api/` (DRF
SessionAuthentication isn't used). Cookie-based JWT is CSRF-safe
because the auth class only trusts the cookie if its value is a
valid signed JWT — a CSRF forgery can't forge a signature.

The `csrftoken` cookie still appears for Django admin; ignore it
from the frontend.

## CORS

Set via env in `packages/api/settings/{dev,prod}.py`:

```
CORS_ALLOWED_ORIGINS=https://photo-feed.gotdns.ch
CSRF_TRUSTED_ORIGINS=https://photo-feed.gotdns.ch
```

In dev, add your dev origin to `packages/api/.env`. Wildcards are
not allowed because credentials-mode requires explicit origins.

## JWT contents

Standard `simplejwt` claims plus `user_id`. No PII beyond what the
frontend already knows.

```json
{
  "token_type": "access",
  "exp": 1717693200,
  "iat": 1717692900,
  "jti": "abc...",
  "user_id": 42
}
```

The backend reads `user_id` and re-fetches `User` per request.
