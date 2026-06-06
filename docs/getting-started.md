# Getting Started

## Install

Install the client SDK and the server:

```bash
pip install smello smello-server
```

Start the server:

```bash
smello-server
```

Or run with Docker:

```bash
docker run -p 127.0.0.1:5110:5110 ghcr.io/smelloscope/smello
```

The server listens at [http://localhost:5110](http://localhost:5110). The `127.0.0.1:` prefix keeps it accessible only from your machine. Omit it if you need LAN access.

!!! tip "Why port 5110?"
    Read it as **5-1-1-0** → **S-L-L-O** → **smello**.

## Run your code with Smello

Prefix any Python command with `smello run`:

```bash
smello run my_app.py
smello run pytest tests/
smello run uvicorn app:app
```

That's it. Smello activates before your code runs and monkey-patches `requests`, `httpx`, `aiohttp`, `grpc`, and `botocore` to capture all outgoing traffic. It also hooks `sys.excepthook` to capture unhandled exceptions. No code changes needed.

Subprocess instrumentation propagates automatically, so `smello run gunicorn app:app` also captures traffic from worker processes.

Use `--` to disambiguate when smello flags conflict with the wrapped command's flags:

```bash
smello run --capture-logs --log-level INFO -- python -m my_module --debug
```

CLI flags map 1:1 to the [environment variables](configuration.md):

| Flag                    | Env var                       |
| ----------------------- | ----------------------------- |
| `--server`              | `SMELLO_URL`                  |
| `--debug` / `--no-debug` | `SMELLO_DEBUG`               |
| `--capture-host`        | `SMELLO_CAPTURE_HOSTS`        |
| `--ignore-host`         | `SMELLO_IGNORE_HOSTS`         |
| `--capture-all` / `--no-capture-all` | `SMELLO_CAPTURE_ALL` |
| `--redact-header`       | `SMELLO_REDACT_HEADERS`       |
| `--redact-query-param`  | `SMELLO_REDACT_QUERY_PARAMS`  |
| `--capture-logs` / `--no-capture-logs` | `SMELLO_CAPTURE_LOGS` |
| `--log-level`           | `SMELLO_LOG_LEVEL`            |
| `--ignore-logger`       | `SMELLO_IGNORE_LOGGERS`       |
| `--app`                 | `SMELLO_APP`                  |
| `--session`             | `SMELLO_SESSION`              |

### Using `smello.init()` instead

If you prefer to activate Smello from within your code, call `smello.init()`:

```python
import smello
smello.init()
```

Smello only activates when a server URL is provided, either via the `server_url` parameter or the `SMELLO_URL` environment variable. Without a URL, `init()` is a safe no-op: no monkey-patching, no background threads, no side effects.

```bash
# Activate in development
export SMELLO_URL=http://localhost:5110
```

Like Sentry's `SENTRY_DSN`, this keeps instrumentation in place with zero production overhead. `smello.init()` is also the right choice for projects with a custom `sitecustomize.py`, where `smello run` can't be used.

### FastAPI middleware

To capture incoming HTTP requests in a FastAPI app, add the Smello middleware:

```python
from smello.integrations.fastapi import SmelloMiddleware
from fastapi import FastAPI

app = FastAPI()
app.add_middleware(SmelloMiddleware)
```

Then run your server with `smello run`:

```bash
smello run uvicorn app:app
```

Every request your server handles appears in the dashboard with method, path, status code, duration, route pattern, and client IP. If a route handler raises an unhandled exception, the middleware captures the traceback before re-raising.

By default, all paths are captured. Use `ignore_paths` to skip noisy endpoints like health checks and OpenAPI schema routes. Matching is prefix-based:

```python
app.add_middleware(SmelloMiddleware, ignore_paths=["/health", "/openapi.json", "/docs"])
```

The middleware is a raw ASGI middleware (not Starlette's `BaseHTTPMiddleware`), so it works with streaming responses and background tasks. When Smello is inactive (no server URL configured), the middleware passes requests through without capturing anything.

### Django middleware

To capture incoming HTTP requests in a Django app, add the Smello middleware at the top of your `MIDDLEWARE` list:

```python
# settings.py
MIDDLEWARE = [
    "smello.integrations.django.SmelloMiddleware",  # first — sees the raw request
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # ...
]
```

Then run your server with `smello run`:

```bash
smello run manage.py runserver
```

Every request your server handles appears in the dashboard with method, path, status code, duration, route pattern, and client IP. If a view raises an unhandled exception, the middleware captures the traceback via Django's `process_exception` hook.

By default, all paths are captured. Use the `SMELLO_IGNORE_PATHS` setting to skip noisy endpoints. Matching is prefix-based:

```python
SMELLO_IGNORE_PATHS = ["/health/", "/admin/", "/static/"]
```

When Smello is inactive (no server URL configured), the middleware passes requests through without capturing anything.

### Capturing logs

Log capture is opt-in. Enable it to see Python log records alongside your HTTP traffic and exceptions in the same timeline:

```bash
smello run --capture-logs --log-level INFO my_app.py
```

Or with `smello.init()`:

```python
import smello
smello.init(capture_logs=True, log_level=20)
```

Smello's own loggers (`smello.*`) and `urllib3` loggers are always excluded to prevent recursion. You can suppress other noisy loggers with `ignore_loggers`:

```bash
smello run --capture-logs --ignore-logger uvicorn.access --ignore-logger uvicorn.error my_app.py
```

Matching is hierarchical: `"uvicorn"` suppresses `uvicorn`, `uvicorn.access`, `uvicorn.error`, etc. See [ignore_loggers](configuration.md#ignore_loggers) for details.

### Capturing exceptions

Unhandled exceptions are captured by default. No configuration needed. When your program crashes, Smello captures the full traceback with stack frames and source context, then flushes the event before the process exits.

To disable exception capture: `smello run --no-capture-exceptions my_app.py` or `smello.init(capture_exceptions=False)`.

### Debugging sessions

Tag events with `--app` and `--session` to isolate a debugging run without clearing existing data:

```bash
smello run --app myapp --session debug-payment python scripts/checkout.py
```

Then filter the dashboard or API to see only events from that session:

```bash
curl -s 'http://localhost:5110/api/events?app=myapp&session=debug-payment'
```

This is useful when you have multiple services or scripts running at the same time — give each its own `--app` name and a shared `--session` to see the full picture. See [configuration](configuration.md#app) for more.

### Google Cloud libraries

Many Google Cloud Python libraries use gRPC under the hood. Smello captures these calls automatically. No extra setup needed:

```bash
smello run my_bigquery_script.py
```

BigQuery, Firestore, Pub/Sub, Analytics (GA4), Vertex AI, Speech-to-Text, Vision, Translation: anything that calls `grpc.secure_channel()` or `grpc.insecure_channel()` is captured.

### AWS libraries (boto3)

boto3 uses `botocore`, which calls `urllib3` directly, bypassing `requests` and `httpx`. Smello patches botocore's HTTP session to capture all AWS API calls:

```bash
smello run my_aws_script.py
```

AWS calls appear at `http://localhost:5110`. XML responses show as a collapsible tree, just like JSON.

## Troubleshooting

If Smello appears to be running but you don't see events in the dashboard, enable debug mode:

```bash
# Via CLI flag
smello run --debug my_app.py

# Via environment variable
SMELLO_DEBUG=1 smello run my_app.py

# In code
smello.init(server_url="http://localhost:5110", debug=True)
```

Debug mode logs to stderr: the resolved configuration and where each value came from, which libraries were patched, every capture/skip decision, and whether the server is reachable. See [configuration](configuration.md#debug) for details.

## What Smello captures

### Outgoing HTTP requests

For every outgoing HTTP and gRPC call:

- Method, URL, headers, and body
- Response status code, headers, and body
- Duration in milliseconds
- Library used (requests, httpx, aiohttp, grpc, or botocore)

The dashboard recognizes Unix timestamps in JSON bodies and shows the human-readable date in a tooltip. XML responses (common in AWS S3, STS, EC2) appear as a collapsible tree, just like JSON. Both formats offer Tree and Raw tabs. Tree shows an expandable tree; Raw shows syntax-highlighted source.

gRPC calls are displayed with a `grpc://` URL scheme. Protobuf request and response bodies are automatically serialized to JSON.

### Incoming HTTP requests

When you add the [FastAPI](#fastapi-middleware) or [Django](#django-middleware) middleware, Smello captures every request your server handles:

- Method, path, full URL, and route pattern (e.g., `/api/users/{id}`)
- Request and response headers and bodies
- Response status code and duration
- Client IP address
- Exception type and traceback (if the handler raises)

Request and response bodies are capped at 1 MB, matching the outgoing capture limit.

### Logs

When `capture_logs=True`, Smello captures Python log records at or above the configured `log_level`:

- Level (DEBUG, INFO, WARNING, ERROR, CRITICAL), logger name, and formatted message
- Source file path, line number, and function name
- Extra attributes attached to the record via `extra={...}`

Smello's own loggers (`smello.*`) and `urllib3` loggers are automatically excluded to prevent recursion.

### Exceptions

Unhandled exceptions are captured with:

- Exception type, message, and module
- Full formatted traceback text
- Individual stack frames with filename, line number, function name, and source context line

Both `sys.excepthook` (main thread) and `threading.excepthook` (worker threads) are hooked.

Smello redacts sensitive headers (`Authorization`, `X-Api-Key`) by default and optionally redacts query string parameters ([details](configuration.md#redact_query_params)).

## Supported libraries

| Library      | What Smello patches                                    |
| ------------ | ------------------------------------------------------ |
| **requests** | `Session.send()`                                       |
| **httpx**    | `Client.send()` and `AsyncClient.send()`               |
| **grpc**     | `insecure_channel()` and `secure_channel()` (unary-unary) |
| **aiohttp**  | `ClientSession._request()` (async HTTP client)         |
| **botocore** | `URLLib3Session.send()` (all boto3 / AWS SDK calls)    |

## Python version support

| Package                 | Python  |
| ----------------------- | ------- |
| **smello** (client SDK) | >= 3.10 |
| **smello-server**       | >= 3.14 |
