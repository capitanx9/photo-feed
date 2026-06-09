# CI (GitHub Actions)

Two workflows guard the codebase. Both run the same `make` targets
you run locally; nothing CI-specific is hidden inside YAML.

| Workflow | File | Source paths |
|---|---|---|
| `ci-api` | [`.github/workflows/ci-api.yml`](../../.github/workflows/ci-api.yml) | `packages/api/**`, root tool config, workflow file |
| `ci-lambdas` | [`.github/workflows/ci-lambdas.yml`](../../.github/workflows/ci-lambdas.yml) | `packages/cut_image/**`, `packages/generate_image/**`, `infra/**`, root tool config, workflow file |

## What they actually run

`ci-api`:

```bash
make lint
make test            # against a Postgres service container
make gen-api-check   # fails if schemas/openapi.yaml drifts from code
```

`ci-lambdas`:

```bash
make lint
make test-lambdas
make sam-validate
make sam-build
```

There are **no AWS credentials** wired into `ci-lambdas` — the SAM
steps validate and build offline. The real deploys are in
[`../deploy/prod-remote.md`](../deploy/prod-remote.md).

## Triggers

```yaml
on:
  push:
    branches: [main]
    paths: [ … see workflow file … ]
  pull_request:
    branches: [main]
    # No paths filter on PRs — see below.
```

### Why no `paths:` on `pull_request:`

Branch protection requires `ci-api` and `ci-lambdas` to report a
status on every PR. If `pull_request` were paths-filtered, a PR that
only touches `infra/` or `.github/workflows/` would skip CI entirely
and the required check would sit "pending" forever — blocking merge.

So: drop `paths:` from `pull_request:` (CI runs on every PR), keep
`paths:` on `push: main` (we don't need to re-run on main when the
change can't affect the package).

## Concurrency

```yaml
concurrency:
  group: ci-api-${{ github.ref }}     # or ci-lambdas-${{ github.ref }}
  cancel-in-progress: true
```

A new commit on the same branch cancels the previous run. CI only
cares about the latest tip.

## Required checks for merging

`main` is protected. A PR can merge only if:

- `ci-api / lint-and-test` — green
- `ci-lambdas / lint-and-test` — green

No required reviewers, no signed-commits. Pre-commit hooks plus
these two checks are the entire contract.
