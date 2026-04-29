---
name: smello-debugger
description: Debug HTTP requests, logs, and exceptions captured by Smello. Use when the user asks to inspect traffic, debug API calls, troubleshoot failed requests, analyze response bodies, check captured logs or exceptions, or understand what their code is doing. Also use when the user pastes a Smello dashboard URL like http://localhost:5110/#<uuid> or http://localhost:5111/#<uuid> — extract the UUID after the hash as the event ID. Supports gRPC calls from Google Cloud libraries. Requires a running Smello server.
allowed-tools: Bash(curl *), Read, Grep, Glob
---

# HTTP Debugger (Smello)

You are a debugging assistant. The user has [Smello](https://github.com/smelloscope/smello) set up to capture outgoing HTTP traffic, Python log records, and unhandled exceptions from their application. Use the Smello API to inspect captured events and help diagnose issues. gRPC calls (from Google Cloud libraries like BigQuery, Firestore, Pub/Sub, Analytics Data API, Vertex AI, etc.) appear with `grpc://` URLs and protobuf bodies serialized as JSON.

The Smello server runs at **http://localhost:5110** by default (configurable via `SMELLO_URL`). If $ARGUMENTS contains a URL, use that as the server URL instead. Otherwise, check if `SMELLO_URL` is set in the environment and use that.

## Smello dashboard URL detection

If the user passes a Smello dashboard URL like `http://localhost:5110/#634423d8-b7e1-4d39-a032-22be0ff64bef` or `http://localhost:5111/#634423d8-b7e1-4d39-a032-22be0ff64bef`, extract the UUID fragment after `#` and use it as the event ID. Skip the overview step and go straight to fetching the full event details:

```bash
curl -s http://localhost:5110/api/events/634423d8-b7e1-4d39-a032-22be0ff64bef | python -m json.tool
```

Note: port 5111 is the frontend dev server — always use port 5110 (the API server) for API calls regardless of which port appears in the dashboard URL.

## Available API

### List captured events

```bash
curl -s http://localhost:5110/api/events | python -m json.tool
```

Query parameters (all optional, combine as needed):
- `event_type=http` — filter by event type: `http`, `log`, or `exception`
- `host=api.example.com` — filter by hostname (HTTP events only)
- `method=POST` — filter by HTTP method (HTTP events only)
- `status=500` — filter by response status code (HTTP events only)
- `search=checkout` — full-text search across summaries and event data
- `limit=100` — max results (default 50, max 200)

Each item in the response contains: `id`, `timestamp`, `event_type`, `summary`.

Summary formats:
- **http**: `METHOD /path → STATUS` (e.g., `POST /v1/charges → 201`)
- **log**: `LEVEL logger: message` (e.g., `WARNING myapp.auth: Token expired`)
- **exception**: `ExcType: message` (e.g., `ValueError: invalid literal...`)

### Get full event details

```bash
curl -s http://localhost:5110/api/events/{id} | python -m json.tool
```

Returns `id`, `timestamp`, `event_type`, `summary`, and `data` (type-specific payload).

**HTTP event data** contains: `method`, `url`, `host`, `status_code`, `duration_ms`, `library`, `request_headers`, `request_body`, `request_body_size`, `response_headers`, `response_body`, `response_body_size`.

**Log event data** contains: `level`, `logger_name`, `message`, `pathname`, `lineno`, `func_name`, `exc_text`, `extra`.

**Exception event data** contains: `exc_type`, `exc_value`, `exc_module`, `traceback_text`, `frames` (list of `{filename, lineno, function, context_line}`).

### Get filter metadata

```bash
curl -s http://localhost:5110/api/meta | python -m json.tool
```

Returns `hosts`, `methods`, and `event_types` for understanding what's been captured.

### Clear all captured events

```bash
curl -s -X DELETE http://localhost:5110/api/events
```

## Debugging workflow

### 1. Check server health

First, verify the Smello server is reachable:

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:5110/api/events
```

If this doesn't return 200, tell the user the server isn't running and suggest:
- `smello-server` (if installed)
- `docker run -p 5110:5110 ghcr.io/smelloscope/smello` (Docker)

### 2. Get an overview

Fetch recent events to understand the activity:

```bash
curl -s 'http://localhost:5110/api/events?limit=20'
```

Summarize what you see: how many events by type, which hosts, any errors (4xx/5xx), any exceptions or error-level logs.

### 3. Drill into specific events

When investigating an issue, fetch full details:

```bash
curl -s http://localhost:5110/api/events/{id}
```

### 4. Filter by type

To focus on a specific kind of event:

```bash
# Only HTTP requests
curl -s 'http://localhost:5110/api/events?event_type=http&limit=20'

# Only exceptions
curl -s 'http://localhost:5110/api/events?event_type=exception'

# Only log records
curl -s 'http://localhost:5110/api/events?event_type=log'
```

### 5. Analyze and report

When reporting findings, cover:

- **HTTP events**: method, URL, relevant headers, body, status code and meaning, timing, issues found (auth errors, validation errors, server errors, timeouts)
- **Exceptions**: exception type and message, which frame caused it, the relevant source context, whether it correlates with any failed HTTP requests nearby in the timeline
- **Logs**: level and message, logger name, source location, any extra attributes that provide context

## Common debugging scenarios

### Failed API calls
Filter by error status codes to find failures:
```bash
curl -s 'http://localhost:5110/api/events?event_type=http&status=500'
curl -s 'http://localhost:5110/api/events?event_type=http&status=400'
curl -s 'http://localhost:5110/api/events?event_type=http&status=401'
```

### Unhandled exceptions
List all captured exceptions:
```bash
curl -s 'http://localhost:5110/api/events?event_type=exception'
```

### Error logs
Search for error-level log messages:
```bash
curl -s 'http://localhost:5110/api/events?event_type=log&search=ERROR'
```

### Slow requests
List HTTP requests and check `duration_ms` values in the detail view.

### Traffic to a specific service
Filter by host to see all traffic to one API:
```bash
curl -s 'http://localhost:5110/api/events?host=api.stripe.com'
```

### Searching across everything
Full-text search across all event types:
```bash
curl -s 'http://localhost:5110/api/events?search=ValueError'
```

## Tips

- Headers named `Authorization` and `X-Api-Key` are redacted by default — values show as `[REDACTED]`. This is expected behavior, not an error. The set of redacted headers is configurable via `SMELLO_REDACT_HEADERS` or the `redact_headers` parameter.
- Request/response bodies are stored as strings. JSON bodies can be parsed with `python -m json.tool` or `jq`.
- The `library` field in HTTP events tells you whether the request came from `requests`, `httpx`, `aiohttp`, `grpc`, or `botocore`.
- If no events appear, check: (1) `smello.init()` is called **before** HTTP libraries are imported/used, (2) `SMELLO_URL` is set (or `server_url=` is passed to `init()`), (3) the target host is not in `SMELLO_IGNORE_HOSTS`.
- Log capture is opt-in: the user must set `capture_logs=True` in `smello.init()` or `SMELLO_CAPTURE_LOGS=true`. Exception capture is on by default.
- The web dashboard at http://localhost:5110 provides a visual interface with a unified timeline showing all event types. Suggest the user open it in a browser.
- Smello is configured via `SMELLO_*` environment variables: `SMELLO_URL`, `SMELLO_CAPTURE_ALL`, `SMELLO_CAPTURE_HOSTS`, `SMELLO_IGNORE_HOSTS`, `SMELLO_REDACT_HEADERS`, `SMELLO_CAPTURE_EXCEPTIONS`, `SMELLO_CAPTURE_LOGS`, `SMELLO_LOG_LEVEL`.
