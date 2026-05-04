# Configuration

`smello.init()` accepts these parameters:

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

Every parameter falls back to a **`SMELLO_*` environment variable** when not passed explicitly, then to a hardcoded default. This follows the same pattern as Sentry (`SENTRY_DSN`) and LangSmith (`LANGSMITH_API_KEY`).

## Parameters

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

**Precedence**: explicit parameter > environment variable > hardcoded default. The same env vars are also surfaced as flags on the [`smello run`](#client-cli-smello-run) wrapper.

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

Header names whose values Smello replaces with `[REDACTED]`. Default: `["Authorization", "X-Api-Key"]`.

Set via env var: `SMELLO_REDACT_HEADERS=Authorization,X-Api-Key,X-Custom-Token` (comma-separated). Setting this replaces the defaults entirely.

### `redact_query_params`

Query parameter names whose values Smello replaces with `[REDACTED]`. Default: `[]`.

Set via env var: `SMELLO_REDACT_QUERY_PARAMS=api_key,token,secret` (comma-separated).

### `capture_exceptions`

Capture unhandled exceptions via `sys.excepthook` and `threading.excepthook`. Default: `True`. Captures the full traceback with stack frames and source context.

Set via env var: `SMELLO_CAPTURE_EXCEPTIONS=false`.

### `capture_logs`

Hook into Python's `logging` module to capture log records. Default: `False` (opt-in). When enabled, Smello patches `logging.Logger.callHandlers` to intercept records at or above `log_level`.

Smello's own loggers (`smello.*`) and `urllib3` loggers are automatically excluded to prevent recursion.

Set via env var: `SMELLO_CAPTURE_LOGS=true`.

### `log_level`

Minimum log level to capture, as an integer. Default: `30` (WARNING). Uses standard Python logging levels: DEBUG=10, INFO=20, WARNING=30, ERROR=40, CRITICAL=50.

Set via env var: `SMELLO_LOG_LEVEL=20` (captures INFO and above).

## Environment-only configuration

For projects where you want zero code changes, add `smello.init()` without arguments and control activation via the `SMELLO_URL` environment variable:

```python
import smello
smello.init()  # activates only when SMELLO_URL is set
```

```bash
export SMELLO_URL=http://localhost:5110
export SMELLO_IGNORE_HOSTS=localhost,internal.svc
export SMELLO_CAPTURE_LOGS=true
export SMELLO_LOG_LEVEL=20
```

Without `SMELLO_URL`, `init()` is a no-op — safe for production. Useful for Docker Compose, CI, and `.env` files.

## Flushing and shutdown

Smello sends captures in a background thread so it never blocks your application. This means your process may exit before all captures reach the server — especially in short-lived scripts or CLI tools.

`smello.init()` registers an `atexit` hook that automatically flushes pending captures (with a 2-second timeout) when the program exits. For exception capture, Smello also flushes synchronously before calling the original `sys.excepthook`, ensuring the crash event reaches the server before the process dies.

For explicit control:

```python
# Block until all pending captures are sent (up to 5 seconds)
smello.flush(timeout=5.0)  # returns True if drained, False if timed out

# Flush and stop the transport
smello.shutdown(timeout=2.0)
```

In test suites or scripts where you need to verify captures arrived, call `smello.flush()` before your assertions.

## Logging

Smello uses Python's standard `logging` module for its own diagnostics. By default it is silent — a `NullHandler` is attached to the `smello` logger so no output is produced unless you opt in.

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

!!! note "Smello diagnostics vs. log capture"
    These are two separate things. **Smello diagnostics** (`logging.getLogger("smello")`) controls Smello's own debug output. **Log capture** (`capture_logs=True`) captures your application's log records and sends them to the dashboard. Smello never captures its own loggers to avoid recursion.

## Client CLI: `smello run`

`smello run` wraps any Python program and activates Smello in the wrapped process without modifying its source. It works by prepending a bootstrap directory to `PYTHONPATH` and executing your command, so subprocess instrumentation propagates automatically — wrapping `gunicorn` patches its workers too.

```bash
# .py files run with the current Python interpreter
smello run my_app.py

# Console scripts work directly
smello run uvicorn app:app
smello run pytest tests/
smello run gunicorn app:app

# Use `--` to disambiguate when the wrapped command's flags conflict with smello's
smello run --server http://localhost:5110 -- python -m my_module --debug
```

Each flag maps 1:1 to a `SMELLO_*` environment variable documented above. The flag wins when both are set:

| Flag                                  | Env variable                  | Default                |
| ------------------------------------- | ----------------------------- | ---------------------- |
| `--server URL`                        | `SMELLO_URL`                  | `http://localhost:5110` |
| `--capture-host HOST` (repeatable)    | `SMELLO_CAPTURE_HOSTS`        | `[]`                   |
| `--ignore-host HOST` (repeatable)     | `SMELLO_IGNORE_HOSTS`         | `[]`                   |
| `--capture-all` / `--no-capture-all`  | `SMELLO_CAPTURE_ALL`          | `True`                 |
| `--redact-header HEADER` (repeatable) | `SMELLO_REDACT_HEADERS`       | `Authorization,X-Api-Key` |
| `--redact-query-param PARAM` (repeatable) | `SMELLO_REDACT_QUERY_PARAMS` | `[]`                  |
| `--capture-exceptions` / `--no-capture-exceptions` | `SMELLO_CAPTURE_EXCEPTIONS`  | `True`                 |
| `--capture-logs` / `--no-capture-logs` | `SMELLO_CAPTURE_LOGS`        | `False`                |
| `--log-level LEVEL`                   | `SMELLO_LOG_LEVEL`           | `30` (WARNING)         |

CLI-specific behavior worth knowing:

- **`.py` script detection**: if the wrapped command ends in `.py` or `.pyw`, `smello run` prepends `sys.executable` so the script runs even without an executable bit or shebang. Same UX as `coverage run script.py`.
- **`--capture-host` implies `--no-capture-all`**: passing `--capture-host` without an explicit `--capture-all` switches the wrapper into "only these hosts" mode. Pass `--capture-all` explicitly if you want both an allowlist and the catch-all.
- **`smello.init()` is idempotent**: wrapping a program that already calls `smello.init()` is safe — the wrapper's bootstrap init runs first, then the program's `init()` updates the live config in place without re-applying patches (no double-capture).
- **Subprocess propagation**: the bootstrap dir stays on `PYTHONPATH` for the lifetime of the process tree, so child Pythons spawned by `subprocess.run([sys.executable, ...])`, `gunicorn` workers, `celery` workers, etc., all get instrumented automatically.

## Server CLI options

```bash
smello-server --host 0.0.0.0 --port 5110 --db-path /tmp/smello.db
```

| Flag        | Default              | Description          |
| ----------- | -------------------- | -------------------- |
| `--host`    | `0.0.0.0`           | Bind address         |
| `--port`    | `5110`               | Port                 |
| `--db-path` | `~/.smello/smello.db` | SQLite database file |
