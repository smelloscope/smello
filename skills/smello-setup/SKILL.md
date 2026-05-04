---
name: smello-setup
description: Explore a Python codebase and propose a plan to integrate Smello — capture HTTP requests, logs, and exceptions in a local web dashboard. Use when the user wants to add Smello to their project, set up request monitoring, debug logging, or capture outgoing API calls and crashes for debugging.
argument-hint: "[server_url]"
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(pip *), Bash(uv *), Bash(cat *), Bash(ls *), Bash(python *), Bash(docker *)
---

# Setup Smello

You are helping the user integrate [Smello](https://github.com/smelloscope/smello) into their Python project. Smello captures outgoing HTTP requests (via `requests`, `httpx`, `aiohttp`, and `botocore`), gRPC calls (via `grpc`), unhandled exceptions (via `sys.excepthook`), and Python log records (via `logging`). Everything is displayed in a unified timeline in a local web dashboard at http://localhost:5110. Google Cloud libraries (BigQuery, Firestore, Pub/Sub, Analytics Data API, Vertex AI, etc.) use gRPC under the hood and are captured automatically.

**Your job is to explore the codebase, then present a plan. Do NOT make any changes until the user approves.**

## Step 1: Explore the codebase

Investigate the project to understand:

1. **Package manager**: Is the project using `pip` + `requirements.txt`, `pip` + `pyproject.toml`, `uv`, `poetry`, `pipenv`, or something else?
2. **HTTP/gRPC libraries**: Does the project use `requests`, `httpx`, `aiohttp`, `grpc`, `botocore`, or Google Cloud client libraries? Search for `import requests`, `import httpx`, `from requests`, `from httpx`, `import grpc`, `from google.cloud`, `from google.analytics`, `import boto3`, `import botocore`.
3. **Logging usage**: Does the project use Python's `logging` module? Search for `import logging`, `logging.getLogger`, `logger.warning`, `logger.error`. This determines whether to suggest `capture_logs=True`.
4. **Application entrypoint**: Find where the app starts. Look for:
   - `if __name__ == "__main__":` blocks
   - Framework-specific entrypoints: Django (`manage.py`, `wsgi.py`, `asgi.py`), Flask (`app = Flask(...)`, `create_app()`), FastAPI (`app = FastAPI()`), etc.
   - CLI entrypoints in `pyproject.toml` (`[project.scripts]`)
5. **Docker setup**: Check for `docker-compose.yml`, `docker-compose.dev.yml`, `compose.yml`, `compose.dev.yml`, `Dockerfile`, or similar files. Identify development-specific compose files vs production ones.
6. **Environment-based config**: Check if the project uses environment variables, `.env` files, or settings modules to toggle dev-only features (this informs where to gate `smello.init()`).

## Step 2: Present the plan

After exploring, present a clear plan with these sections:

### A. Install the packages

The recommended approach is to install `smello` as a **regular (not dev) dependency**. It has zero dependencies itself, and `smello.init()` is a safe no-op when `SMELLO_URL` is not set — no patching, no threads, no side effects. This means users don't need conditional imports or `try/except ImportError` guards in production.

Based on the package manager detected:

- **pip + requirements.txt**: `pip install smello` (add `smello` to `requirements.txt`)
- **pip + pyproject.toml**: Add `smello` to `[project.dependencies]`
- **uv**: `uv add smello`
- **poetry**: `poetry add smello`
- **pipenv**: `pipenv install smello`

The server is covered separately in section D below.

### B. Pick an activation path

Smello can be activated in two ways. Recommend **one** based on what fits the project; mention the other so the user knows it exists.

**Path 1 — code-level activation (`smello.init()`)**: explicit, lives next to other bootstrap code, easy to gate by environment. Best when the project owns its entrypoint and a couple of extra lines are welcome.

**Path 2 — wrapper (`smello run`)**: zero source changes. The user prepends `smello run` to whatever command they already use (`smello run uvicorn app:app`, `smello run pytest tests/`, `smello run my_app.py`). Best when:
- The entrypoint is owned by a framework or third-party tool that's awkward to edit (gunicorn/uvicorn workers, pytest, celery).
- The user just wants a one-off debugging session and doesn't want to touch source.
- Subprocess instrumentation needs to propagate to workers automatically (it does — PYTHONPATH is inherited).

`smello run` exposes the same `SMELLO_*` config as flags: `--server`, `--capture-host`, `--ignore-host`, `--capture-all`/`--no-capture-all`, `--redact-header`, `--redact-query-param`, `--capture-exceptions`/`--no-capture-exceptions`, `--capture-logs`/`--no-capture-logs`, `--log-level`. Flags win over env vars. Use `--` to disambiguate when the wrapped command's flags would collide (`smello run --server URL -- python -m mod --debug`).

#### B1. If using `smello.init()`

Propose the exact file and location. The two lines must go **before** any HTTP library imports or usage so HTTP patching catches the first request:

```python
import smello
smello.init()
```

Ordering nuance for the other capture types:

- **Exceptions** (on by default — `capture_exceptions=True`): `init()` installs `sys.excepthook` / `threading.excepthook` immediately. Position doesn't matter beyond running before the exception happens — for unhandled exceptions in the bootstrap path itself, place `init()` as early as possible. Pass `capture_exceptions=False` (or `SMELLO_CAPTURE_EXCEPTIONS=false`) to opt out.
- **Logs** (off by default — opt in with `capture_logs=True`): logging capture works regardless of when handlers and loggers are created — Smello hooks `Logger.callHandlers`, which all log calls funnel through. So even loggers configured later (Django settings, `logging.config.dictConfig`, etc.) are captured.

Common placement patterns:

- **Django**: In `manage.py` (for `runserver`) or a custom `AppConfig.ready()` method
- **Flask**: At the top of `create_app()` or the app factory
- **FastAPI**: At module level in the main app file, or in a `lifespan` handler
- **CLI / script**: Near the top of `if __name__ == "__main__":`
- **General**: Wherever the application bootstraps, before HTTP calls are made

Since Smello uses the server URL as its activation signal, the recommended pattern is to always call `smello.init()` and control activation via the `SMELLO_URL` environment variable:

```python
import smello
smello.init()  # only activates when SMELLO_URL is set
```

Then in `.env` or the shell:

```bash
SMELLO_URL=http://localhost:5110
```

This way the code has zero conditional logic — without `SMELLO_URL`, `init()` is a safe no-op (no patching, no threads, no side effects).

If the project uses logging extensively, suggest enabling log capture:

```python
import smello
smello.init(capture_logs=True, log_level=20)  # capture INFO and above
```

Or via environment variables:

```bash
SMELLO_CAPTURE_LOGS=true
SMELLO_LOG_LEVEL=20
```

Exception capture is enabled by default — no configuration needed.

#### B2. If using `smello run`

No source edits. The user runs their existing command through the wrapper:

```bash
# .py scripts run with the current Python interpreter
smello run my_app.py

# Console scripts work directly; subprocess workers are instrumented automatically
smello run uvicorn app:app
smello run gunicorn app:app
smello run pytest tests/

# `--` disambiguates when the wrapped command and smello share flag names
smello run --server http://localhost:5110 -- python -m my_module --debug

# Enable log + exception capture without code changes
smello run --capture-logs --log-level 20 uvicorn app:app
```

If the project ships its own `smello.init()` call already, the wrapper is still safe to use: bootstrap initialization runs first, then the program's `init()` updates the live config in place (no double-patching, no double-capture).

For long-running commands defined in `Procfile`, `Makefile`, `justfile`, `package.json` scripts, or compose files, suggest prefixing the command with `smello run` in dev variants only.

### C. Configure via environment variables

Smello supports full configuration via `SMELLO_*` environment variables. Suggest adding these to the project's `.env`, `.env.development`, or equivalent:

```bash
SMELLO_URL=http://localhost:5110                  # server URL (activates Smello)
# SMELLO_CAPTURE_HOSTS=api.stripe.com,api.openai.com  # only capture these hosts
# SMELLO_IGNORE_HOSTS=localhost,internal.svc      # skip these hosts
# SMELLO_REDACT_HEADERS=Authorization,X-Api-Key   # headers to redact
# SMELLO_CAPTURE_LOGS=true                         # capture Python log records
# SMELLO_LOG_LEVEL=20                              # minimum log level (INFO=20, WARNING=30)
```

All parameters can also be passed explicitly to `smello.init()`, which takes precedence over env vars:

- If the app talks to specific APIs, suggest `SMELLO_CAPTURE_HOSTS=api.example.com` or `capture_hosts=["api.example.com"]`
- If there are internal services to skip, suggest `SMELLO_IGNORE_HOSTS=...` or `ignore_hosts=[...]`
- If a non-default server URL is needed (e.g., Docker networking), suggest `SMELLO_URL=http://smello:5110` or `server_url="http://smello:5110"`
- If the project uses logging heavily, suggest `SMELLO_CAPTURE_LOGS=true` with an appropriate `SMELLO_LOG_LEVEL`
- Always mention that `Authorization` and `X-Api-Key` headers are redacted by default
- Mention that unhandled exception capture is on by default

Boolean env vars accept `true`/`1`/`yes` and `false`/`0`/`no` (case-insensitive). List env vars are comma-separated.

### D. Set up the server

**Ask the user** which server setup they prefer:

1. **No server setup** — they'll install and run `smello-server` separately (skip this section)
2. **Docker Compose** — add a Smello service to their compose file
3. **Development dependency** — add `smello-server` to their project's dev dependencies

`pip install smello-server` includes the full web dashboard — Docker is not required for the UI.

#### Option: Docker Compose

If the user chooses Docker Compose, propose adding a Smello service:

```yaml
smello:
  image: ghcr.io/smelloscope/smello
  ports:
    - "5110:5110"
  volumes:
    - smello-data:/data
```

And add `smello-data` to the `volumes:` section. The app container should set `SMELLO_URL=http://smello:5110` (or pass `server_url="http://smello:5110"` to `init()`) to reach the Smello server over the Docker network.

Prefer adding this to a dev-specific compose file (`docker-compose.dev.yml`, `compose.dev.yml`, `compose.override.yml`) if one exists. If only a single compose file exists, note that the user may want to create a dev overlay.

#### Option: Development dependency

If the user chooses to add the server as a dev dependency, use the same package manager pattern from section A:

- **pip + requirements.txt**: Add `smello-server` to `requirements-dev.txt`
- **pip + pyproject.toml**: Add `smello-server` to the dev dependency group
- **uv**: `uv add --dev smello-server`
- **poetry**: `poetry add --group dev smello-server`
- **pipenv**: `pipenv install --dev smello-server`

Then run with `smello-server`, or as a standalone tool:

```bash
# With uv
uv tool install smello-server

# With pipx
pipx install smello-server
```

## Step 3: Wait for approval

After presenting the plan, ask the user which parts they want to proceed with. Do NOT edit any files until explicitly told to do so.

## Reference

- Smello client SDK: `pip install smello` (Python >= 3.10, zero dependencies)
- Smello server: `pip install smello-server` (Python >= 3.14, includes web dashboard) or Docker `ghcr.io/smelloscope/smello`
- Dashboard: http://localhost:5110 (served by both pip install and Docker)
- Captures: HTTP requests (`requests`, `httpx`, `aiohttp`, `grpc`, `botocore`), unhandled exceptions (`sys.excepthook`), and Python log records (`logging`)
- Default redacted headers: `Authorization`, `X-Api-Key`
- Default server URL: `http://localhost:5110`
- `smello run` wrapper: zero-code activation via `PYTHONPATH` bootstrap; subprocess-instrumentation safe; flags mirror `SMELLO_*` env vars 1:1.

### Environment variables

| Variable | Type | Default |
|----------|------|---------|
| `SMELLO_URL` | string | `None` (inactive) |
| `SMELLO_CAPTURE_ALL` | bool | `true` |
| `SMELLO_CAPTURE_HOSTS` | comma-separated list | `[]` |
| `SMELLO_IGNORE_HOSTS` | comma-separated list | `[]` |
| `SMELLO_REDACT_HEADERS` | comma-separated list | `Authorization,X-Api-Key` |
| `SMELLO_REDACT_QUERY_PARAMS` | comma-separated list | `[]` |
| `SMELLO_CAPTURE_EXCEPTIONS` | bool | `true` |
| `SMELLO_CAPTURE_LOGS` | bool | `false` |
| `SMELLO_LOG_LEVEL` | int | `30` (WARNING) |

Precedence: explicit `init()` parameter > env var > hardcoded default.
