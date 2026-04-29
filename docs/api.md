# API

Smello Server provides a JSON API for exploring captured events from the command line.

The full OpenAPI specification is available at [http://localhost:5110/openapi.json](http://localhost:5110/openapi.json), and an interactive playground at [http://localhost:5110/docs](http://localhost:5110/docs).

## List events

```bash
curl -s http://localhost:5110/api/events | python -m json.tool
```

### Query parameters

| Parameter    | Example          | Description                                   |
| ------------ | ---------------- | --------------------------------------------- |
| `event_type` | `log`            | Filter by event type: `http`, `log`, or `exception` |
| `method`     | `POST`           | Filter by HTTP method (HTTP events only)      |
| `host`       | `api.stripe.com` | Filter by hostname (HTTP events only)         |
| `status`     | `500`            | Filter by response status code (HTTP events only) |
| `search`     | `ValueError`     | Full-text search across summaries and event data |
| `limit`      | `10`             | Max results (default: 50, max: 200)           |

Combine filters:

```bash
curl -s 'http://localhost:5110/api/events?event_type=http&method=POST&host=api.stripe.com&limit=5'
```

### Response format

Each event in the list contains a summary and type:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-04-12T21:00:02.560821Z",
  "event_type": "http",
  "summary": "GET /v1/charges → 200"
}
```

Summary formats by event type:

- **http**: `METHOD /path → STATUS` (e.g., `POST /v1/charges → 201`)
- **log**: `LEVEL logger: message` (e.g., `WARNING myapp.auth: Token expired`)
- **exception**: `ExcType: message` (e.g., `ValueError: invalid literal...`)

## Get event details

Returns the full event data — the shape of `data` depends on the event type.

```bash
curl -s http://localhost:5110/api/events/{id} | python -m json.tool
```

### HTTP event data

```json
{
  "method": "GET",
  "url": "https://api.stripe.com/v1/charges",
  "host": "api.stripe.com",
  "status_code": 200,
  "duration_ms": 142,
  "library": "requests",
  "request_headers": { "Content-Type": "application/json" },
  "request_body": null,
  "response_headers": { "Content-Type": "application/json" },
  "response_body": "{\"id\": \"ch_123\"}"
}
```

### Log event data

```json
{
  "level": "WARNING",
  "logger_name": "myapp.auth",
  "message": "Token expired for user 42",
  "pathname": "/app/auth.py",
  "lineno": 87,
  "func_name": "validate_token",
  "extra": { "user_id": 42 }
}
```

### Exception event data

```json
{
  "exc_type": "ValueError",
  "exc_value": "invalid literal for int()",
  "exc_module": "builtins",
  "traceback_text": "Traceback (most recent call last):\n  ...",
  "frames": [
    {
      "filename": "app.py",
      "lineno": 42,
      "function": "main",
      "context_line": "    x = int(user_input)"
    }
  ]
}
```

## Get filter metadata

Returns distinct hosts, methods, and event types for populating filter dropdowns.

```bash
curl -s http://localhost:5110/api/meta | python -m json.tool
```

```json
{
  "hosts": ["api.openai.com", "api.stripe.com"],
  "methods": ["GET", "POST"],
  "event_types": ["exception", "http", "log"]
}
```

## Clear all events

```bash
curl -X DELETE http://localhost:5110/api/events
```

## Legacy endpoints

The original `/api/requests` endpoints still work for backwards compatibility. They behave identically to `/api/events` but automatically filter to HTTP events only:

```bash
curl -s http://localhost:5110/api/requests              # same as ?event_type=http
curl -s http://localhost:5110/api/requests/{id}          # same as /api/events/{id}
curl -X DELETE http://localhost:5110/api/requests        # clears all event types
```
