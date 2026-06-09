# Bruno

Bruno is the team's API client. Versioned, file-based — the
collection lives in the repo at
[`bruno/photo-feed/`](../../bruno/photo-feed/), so it evolves with
the codebase the same way the OpenAPI spec does.

## Install the desktop app

Download the installer for your OS from
<https://www.usebruno.com/downloads> and run it.

No account, no cloud sync — the app reads collections straight off
disk.

## Open the collection

Launch Bruno → **Open Collection** → point at the repo's
[`bruno/photo-feed/`](../../bruno/photo-feed/) directory.

That's it — no import, no JSON paste. Every `.bru` file in that
directory is a request; folders group them by feature
(`auth/`, `posts/`, `cart/`, `orders/`, etc.).

Pulling new requests from `main` is just `git pull` — Bruno picks up
the file changes immediately.

## Environments

The collection ships two:

| Environment | Base URL |
|---|---|
| `local` | `http://localhost:8000` |
| `prod` | `https://photo-feed.gotdns.ch` |

Switch via the environment selector at the top of the Bruno window.
Each request uses `{{baseUrl}}` so the same `.bru` file works
against either side.

## Cookies

Bruno persists cookies per environment, just like a browser. Run
`auth/login.bru` once and every subsequent request in the same
environment carries the `access` and `refresh` cookies
automatically.

When the cookie expires you'll see `401` — re-run
`auth/login.bru` or `auth/refresh.bru` and keep going.

## How to actually use it

The debugging workflow — Bruno on one side, `make logs-web` on the
other — is in [`../debug/api-testing.md`](../debug/api-testing.md).
