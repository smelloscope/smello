<p align="center">
  <img src="https://raw.githubusercontent.com/smelloscope/smello/main/docs/assets/logo.png" alt="Smello logo" width="160">
</p>

# Smello

Capture outgoing and incoming HTTP requests, Python logs, and unhandled exceptions in a local web dashboard.

Like [Mailpit](https://mailpit.axllent.org/), but for your entire debug output.

## Setup

Install the client SDK and the server:

```bash
pip install smello smello-server
```

Start the server:

```bash
smello-server
```

Run your code with Smello:

```bash
smello run my_app.py
smello run pytest tests/
smello run uvicorn app:app
```

That's it. Smello activates before your code runs and monkey-patches `requests`, `httpx`, `aiohttp`, `grpc`, and `botocore` to capture outgoing traffic. It also hooks `sys.excepthook` to capture unhandled exceptions with full tracebacks, and optionally captures Python log records. No code changes needed.

Subprocess instrumentation propagates automatically through `PYTHONPATH`, so `smello run gunicorn app:app` also captures traffic from worker processes.

CLI flags map 1:1 to the `SMELLO_*` env vars: `--server`, `--capture-host`, `--ignore-host`, `--capture-all` / `--no-capture-all`, `--redact-header`, `--redact-query-param`, `--capture-logs`, `--log-level`.

### Using `smello.init()` instead

If you prefer to activate Smello from within your code (e.g., for programmatic configuration or projects with a custom `sitecustomize.py`):

```python
import smello
smello.init()  # activates only when SMELLO_URL is set
```

### Framework middleware

To capture incoming requests, add the Smello middleware to your web framework:

**FastAPI:**

```python
from smello.integrations.fastapi import SmelloMiddleware
from fastapi import FastAPI

app = FastAPI()
app.add_middleware(SmelloMiddleware, ignore_paths=["/health"])
```

**Django:**

```python
# settings.py
MIDDLEWARE = [
    "smello.integrations.django.SmelloMiddleware",
    ...
]
SMELLO_IGNORE_PATHS = ["/health/", "/admin/"]
```

Then run with `smello run`:

```bash
smello run uvicorn app:app        # FastAPI
smello run manage.py runserver    # Django
```

The middleware captures method, path, status code, duration, route pattern, client IP, and request/response bodies. Unhandled exceptions are captured with full tracebacks. When Smello is inactive (no server URL configured), the middleware passes requests through without capturing anything.

### Google Cloud libraries

Many Google Cloud Python libraries — BigQuery, Firestore, Pub/Sub, Analytics Data API (GA4), Vertex AI, Speech-to-Text, Vision, Translation, and others — use gRPC under the hood. Smello captures these calls automatically:

```bash
smello run my_bigquery_script.py
```

Any library that calls `grpc.secure_channel()` or `grpc.insecure_channel()` is automatically captured.

## What Smello captures

**Outgoing HTTP requests** — method, URL, headers, body, response status/headers/body, duration, and library used (requests, httpx, aiohttp, grpc, or botocore).

**Incoming HTTP requests** (via FastAPI or Django middleware) — method, path, route pattern, status code, duration, client IP, request/response headers and bodies, plus exception tracebacks if a handler raises.

**Unhandled exceptions** (enabled by default) — exception type, message, full traceback, and stack frames with source context.

**Log records** (opt-in via `capture_logs=True`) — level, logger name, message, source location, and extra attributes.

Smello redacts sensitive headers (`Authorization`, `X-Api-Key`) by default and optionally redacts query string parameters.

## Configuration

```python
smello.init(
    server_url="http://localhost:5110",       # where to send captured data

    # HTTP capture
    capture_hosts=["api.stripe.com"],         # only capture these hosts
    capture_all=True,                          # capture everything (default)
    ignore_hosts=["localhost"],               # skip these hosts
    redact_headers=["Authorization"],         # replace header values with [REDACTED]
    redact_query_params=["api_key", "token"], # replace query param values with [REDACTED]

    # Logs & exceptions
    capture_exceptions=True,                   # capture unhandled exceptions (default)
    capture_logs=False,                        # capture log records (opt-in)
    log_level=30,                              # minimum log level to capture (WARNING)
    ignore_loggers=["uvicorn.access"],         # suppress noisy framework loggers
)
```

All parameters fall back to `SMELLO_*` environment variables when not passed explicitly:

| Parameter | Env variable | Default |
|-----------|-------------|---------|
| `server_url` | `SMELLO_URL` | `None` (inactive) |
| `capture_all` | `SMELLO_CAPTURE_ALL` | `True` |
| `capture_hosts` | `SMELLO_CAPTURE_HOSTS` | `[]` |
| `ignore_hosts` | `SMELLO_IGNORE_HOSTS` | `[]` |
| `redact_headers` | `SMELLO_REDACT_HEADERS` | `["Authorization", "X-Api-Key"]` |
| `redact_query_params` | `SMELLO_REDACT_QUERY_PARAMS` | `[]` |
| `capture_exceptions` | `SMELLO_CAPTURE_EXCEPTIONS` | `True` |
| `capture_logs` | `SMELLO_CAPTURE_LOGS` | `False` |
| `log_level` | `SMELLO_LOG_LEVEL` | `30` (WARNING) |
| `ignore_loggers` | `SMELLO_IGNORE_LOGGERS` | `[]` |

The server URL is the activation signal — `init()` does nothing unless `server_url` is passed or `SMELLO_URL` is set. Boolean env vars accept `true`/`1`/`yes` and `false`/`0`/`no` (case-insensitive). List env vars are comma-separated.

## Supported libraries

- **requests** — patches `Session.send()`
- **httpx** — patches `Client.send()` and `AsyncClient.send()`
- **aiohttp** — patches `ClientSession._request()` to capture async HTTP traffic
- **grpc** — patches `insecure_channel()` and `secure_channel()` to intercept unary-unary calls
- **botocore** — patches `URLLib3Session.send()` to capture boto3 / AWS SDK traffic

## Requires

- Python >= 3.10
- [smello-server](https://pypi.org/project/smello-server/) running locally

## Links

- [Documentation](https://smello.io)
- [Source & Issues](https://github.com/smelloscope/smello)
- [Changelog](https://github.com/smelloscope/smello/blob/main/clients/python/CHANGELOG.md)
- [smello-server on PyPI](https://pypi.org/project/smello-server/)
