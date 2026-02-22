# Configuration

`smello.init()` accepts these parameters:

```python
smello.init(
    server_url="http://localhost:5110",       # where to send captured data
    capture_hosts=["api.stripe.com"],         # only capture these hosts
    capture_all=True,                          # capture everything (default)
    ignore_hosts=["localhost"],               # skip these hosts
    redact_headers=["Authorization"],         # replace values with [REDACTED]
)
```

Every parameter falls back to a **`SMELLO_*` environment variable** when not passed explicitly, then to a hardcoded default. This follows the same pattern as Sentry (`SENTRY_DSN`) and LangSmith (`LANGSMITH_API_KEY`).

## Parameters

| Parameter | Env variable | Default |
|-----------|-------------|---------|
| `server_url` | `SMELLO_URL` | `None` (inactive) |
| `capture_all` | `SMELLO_CAPTURE_ALL` | `True` |
| `capture_hosts` | `SMELLO_CAPTURE_HOSTS` | `[]` |
| `ignore_hosts` | `SMELLO_IGNORE_HOSTS` | `[]` |
| `redact_headers` | `SMELLO_REDACT_HEADERS` | `["Authorization", "X-Api-Key"]` |

**Precedence**: explicit parameter > environment variable > hardcoded default.

### `server_url`

URL of the Smello server and the activation signal — without a URL, `init()` does nothing. No patching, no background threads, no side effects.

Set via env var: `SMELLO_URL=http://smello:5110`.

### `capture_hosts`

List of hostnames to capture. When set, Smello only captures requests to these hosts and ignores everything else.

Set via env var: `SMELLO_CAPTURE_HOSTS=api.stripe.com,api.openai.com` (comma-separated).

### `capture_all`

Capture requests to all hosts. Default: `True`. Set to `False` when using `capture_hosts`.

Set via env var: `SMELLO_CAPTURE_ALL=false`.

### `ignore_hosts`

List of hostnames to skip. Smello always ignores the server's own hostname to prevent recursion.

Set via env var: `SMELLO_IGNORE_HOSTS=localhost,internal.svc` (comma-separated).

### `redact_headers`

Header names whose values are replaced with `[REDACTED]`. Default: `["Authorization", "X-Api-Key"]`.

Set via env var: `SMELLO_REDACT_HEADERS=Authorization,X-Api-Key,X-Custom-Token` (comma-separated). Setting this replaces the defaults entirely.

## Environment-only configuration

For projects where you want zero code changes, add `smello.init()` without arguments and control activation via the `SMELLO_URL` environment variable:

```python
import smello
smello.init()  # activates only when SMELLO_URL is set
```

```bash
export SMELLO_URL=http://localhost:5110
export SMELLO_IGNORE_HOSTS=localhost,internal.svc
```

Without `SMELLO_URL`, `init()` is a no-op — safe for production. Useful for Docker Compose, CI, and `.env` files.

## Flushing and shutdown

Smello sends captures in a background thread so it never blocks your application. This means your process may exit before all captures reach the server — especially in short-lived scripts or CLI tools.

`smello.init()` registers an `atexit` hook that automatically flushes pending captures (with a 2-second timeout) when the program exits. For most applications, this is all you need.

For explicit control:

```python
# Block until all pending captures are sent (up to 5 seconds)
smello.flush(timeout=5.0)  # returns True if drained, False if timed out

# Flush and stop the transport
smello.shutdown(timeout=2.0)
```

In test suites or scripts where you need to verify captures arrived, call `smello.flush()` before your assertions.

## Logging

Smello uses Python's standard `logging` module. By default it is silent — a `NullHandler` is attached to the `smello` logger so no output is produced unless you opt in.

To see warnings (dropped payloads, server connectivity issues):

```python
import logging
logging.basicConfig()
logging.getLogger("smello").setLevel(logging.WARNING)
```

To see all debug output (every capture attempt):

```python
import logging
logging.basicConfig()
logging.getLogger("smello").setLevel(logging.DEBUG)
```

You can also route Smello logs to a file or integrate them with your application's existing logging configuration — just configure the `"smello"` logger however you like.

## Server CLI options

```bash
smello-server run --host 0.0.0.0 --port 5110 --db-path /tmp/smello.db
```

| Flag        | Default     | Description          |
| ----------- | ----------- | -------------------- |
| `--host`    | `127.0.0.1` | Bind address         |
| `--port`    | `5110`      | Port                 |
| `--db-path` | `smello.db` | SQLite database file |
