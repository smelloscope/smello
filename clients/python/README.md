<p align="center">
  <img src="https://raw.githubusercontent.com/smelloscope/smello/main/docs/assets/logo.png" alt="Smello logo" width="160">
</p>

# Smello

Capture HTTP requests, Python logs, and unhandled exceptions from your code and browse them in a local web dashboard.

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

Add two lines to your code:

```python
import smello
smello.init(server_url="http://localhost:5110")

import requests
resp = requests.get("https://api.stripe.com/v1/charges")

# Browse captured events at http://localhost:5110
```

Smello monkey-patches `requests`, `httpx`, `aiohttp`, `grpc`, and `botocore` to capture outgoing traffic. It also hooks into `sys.excepthook` to capture unhandled exceptions with full tracebacks, and optionally into Python's `logging` module to capture log records.

Or leave `smello.init()` without arguments and set `SMELLO_URL` in your environment — no URL, no side effects.

### Run without modifying code

For programs you don't want to (or can't) edit, wrap them with `smello run`:

```bash
smello run my_app.py                                    # .py files run with current Python
smello run --server http://localhost:5110 pytest tests/  # console scripts work directly
smello run uvicorn app:app
```

Smello activates in the wrapped process before user code runs. Subprocess instrumentation propagates automatically through `PYTHONPATH`, so wrapping `gunicorn` also captures traffic from worker processes.

CLI flags map 1:1 to the `SMELLO_*` env vars: `--server`, `--capture-host`, `--ignore-host`, `--capture-all` / `--no-capture-all`, `--redact-header`, `--redact-query-param`.

### Google Cloud libraries

Many Google Cloud Python libraries — BigQuery, Firestore, Pub/Sub, Analytics Data API (GA4), Vertex AI, Speech-to-Text, Vision, Translation, and others — use gRPC under the hood. Smello captures these calls automatically:

```python
import smello
smello.init(server_url="http://localhost:5110")

from google.cloud import bigquery
client = bigquery.Client()
rows = client.query("SELECT 1").result()

# gRPC calls to bigquery.googleapis.com appear at http://localhost:5110
```

Any library that calls `grpc.secure_channel()` or `grpc.insecure_channel()` is automatically captured.

## What Smello Captures

**HTTP requests** — method, URL, headers, body, response status/headers/body, duration, and library used (requests, httpx, aiohttp, grpc, or botocore).

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

The server URL is the activation signal — `init()` does nothing unless `server_url` is passed or `SMELLO_URL` is set. Boolean env vars accept `true`/`1`/`yes` and `false`/`0`/`no` (case-insensitive). List env vars are comma-separated.

## Supported Libraries

- **requests** — patches `Session.send()`
- **httpx** — patches `Client.send()` and `AsyncClient.send()`
- **aiohttp** — patches `ClientSession._request()` to capture async HTTP traffic
- **grpc** — patches `insecure_channel()` and `secure_channel()` to intercept unary-unary calls
- **botocore** — patches `URLLib3Session.send()` to capture boto3 / AWS SDK traffic

## Requires

- Python >= 3.10
- [smello-server](https://pypi.org/project/smello-server/) running locally

## Links

- [Documentation & Source](https://github.com/smelloscope/smello)
- [smello-server on PyPI](https://pypi.org/project/smello-server/)
