# Testing

Two suites — api and lambdas. Same workspace, separate `make`
targets, separate dependencies at runtime.

## Commands

| Command | Runs | Notes |
|---|---|---|
| `make test` | api pytest suite | Needs Postgres + Redis up (`make up` first) |
| `make test-cov` | api with coverage report | Same prereqs as `make test` |
| `make test-lambdas` | both Lambda suites | No Django, no DB; moto-backed boto3 |
| `make check` | `make lint` + `make test` | Same gate as `ci-api` runs locally |
| `make test-real-bedrock` | smoke against real Bedrock + S3 | Opt-in only. Costs ~$0.04/run. Needs `aws sso login` first |

## Where the tests live

```
packages/api/tests/             # Django + DRF
packages/cut_image/tests/       # cut_image Lambda
packages/generate_image/tests/  # generate_image Lambda
conftest.py                     # shared fixtures at repo root
```

## What each suite hits

### `make test` (api)

- Postgres — **real**, on `localhost:5432` (dev compose service).
- Redis — **real**, on `localhost:6379`.
- boto3 / S3 — mocked via `moto`. No network.
- Bedrock — mocked.
- Lambda invoke — mocked.

`packages/api/pyproject.toml` sets `pythonpath = ["src"]` for pytest
so `import api` resolves the same way `manage.py runserver` resolves it.

### `make test-lambdas`

- No Django, no Postgres, no Redis.
- boto3 / S3 — `moto`-backed (`@mock_s3`).
- Bedrock — stub via `unittest.mock`.
- Webhook to Django — `requests_mock`.

Lambda tests run anywhere with no infra deps. They don't exercise the
real Lambda runtime — use `make sam-invoke-cut` /
`make sam-invoke-generate` for that.

## Markers worth knowing

```python
@pytest.mark.real_bedrock   # opt-in, hits real Bedrock; costs money
```

`make test` and `make test-lambdas` skip these. `make test-real-bedrock`
adds `-m real_bedrock` to opt in.

## CI runs the same commands

`ci-api`:

```bash
make lint
make test
make gen-api-check
```

`ci-lambdas`:

```bash
make lint
make test-lambdas
make sam-validate
make sam-build
```

If `make check` is green locally, `ci-api` will be green. If
`make test-lambdas && make sam-validate && make sam-build` is green
locally, `ci-lambdas` will be green.
