# pre-commit hooks

Config: [`.pre-commit-config.yaml`](../../.pre-commit-config.yaml) plus
a custom `commit-msg` hook for AI-coauthorship.

## Install (once per clone)

```bash
pre-commit install --install-hooks
pre-commit install --hook-type commit-msg
```

## What runs on `git commit`

From `.pre-commit-config.yaml`:

| Hook | What it does |
|---|---|
| `trailing-whitespace` | Strips trailing whitespace (auto-fix) |
| `end-of-file-fixer` | Ensures one final newline (auto-fix) |
| `check-yaml` | Parses tracked YAML files |
| `check-toml` | Parses tracked TOML files |
| `check-merge-conflict` | Refuses `<<<<<<<` markers |
| `check-added-large-files` | Flags new files > 512 KB |
| `mixed-line-ending` | Forces LF |
| `ruff --fix` | Lint + auto-fix Python |
| `ruff-format` | Format Python |
| `detect-secrets` | Compare new strings against `.secrets.baseline` |

### Custom `commit-msg` hook

Blocks commits whose message contains AI co-authorship trailers.
Patterns (case-insensitive):

- `^[[:space:]]*Co-Authored-By:`
- `noreply@anthropic\.com`

To override for a genuinely co-authored squash:

```bash
ALLOW_AI_COAUTHOR=1 git commit ...
```

## Run hooks against the whole repo

Before opening a big PR:

```bash
pre-commit run --all-files
```

## Skip a single hook ad-hoc

```bash
SKIP=ruff git commit -m "wip"
SKIP=detect-secrets git commit -m "fixture, not a real secret"
```

`SKIP` accepts a comma-separated list. Everything not listed still runs.

## Update hook versions

Periodically:

```bash
pre-commit autoupdate
git diff .pre-commit-config.yaml          # review
pre-commit run --all-files                # make sure nothing broke
```
