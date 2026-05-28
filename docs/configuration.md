# Configuration

`smello.init()` accepts these parameters:

```python
smello.init(
    server_url="http://localhost:5110",       # where to send captured data
    debug=True,                                # log config, patches, and captures to stderr

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

    # Tagging
    app="payment-service",                     # tag events with an application name
    session="debug-payment-flow",              # tag events with a session ID
)
```

Every parameter falls back to a **`SMELLO_*` environment variable** when not passed explicitly, then to a hardcoded default. This follows the same pattern as Sentry (`SENTRY_DSN`) and LangSmith (`LANGSMITH_API_KEY`).

## Parameters

| Parameter | Env variable | CLI flag | Default |
|-----------|-------------|----------|---------|
| `server_url` | `SMELLO_URL` | `--server URL` | `None` (inactive) |
| `debug` | `SMELLO_DEBUG` | `--debug` / `--no-debug` | `False` |
| `capture_all` | `SMELLO_CAPTURE_ALL` | `--capture-all` / `--no-capture-all` | `True` |
| `capture_hosts` | `SMELLO_CAPTURE_HOSTS` | `--capture-host HOST` | `[]` |
| `ignore_hosts` | `SMELLO_IGNORE_HOSTS` | `--ignore-host HOST` | `[]` |
| `redact_headers` | `SMELLO_REDACT_HEADERS` | `--redact-header HEADER` | `["Authorization", "X-Api-Key"]` |
| `redact_query_params` | `SMELLO_REDACT_QUERY_PARAMS` | `--redact-query-param PARAM` | `[]` |
| `capture_exceptions` | `SMELLO_CAPTURE_EXCEPTIONS` | `--capture-exceptions` / `--no-...` | `True` |
| `capture_logs` | `SMELLO_CAPTURE_LOGS` | `--capture-logs` / `--no-capture-logs` | `False` |
| `log_level` | `SMELLO_LOG_LEVEL` | `--log-level LEVEL` | `30` (WARNING) |
| `ignore_loggers` | `SMELLO_IGNORE_LOGGERS` | `--ignore-logger LOGGER` | `[]` |
| `app` | `SMELLO_APP` | `--app NAME` | `""` |
| `session` | `SMELLO_SESSION` | `--session ID` | `""` |

CLI flags marked with `HOST`, `HEADER`, `LOGGER`, or `PARAM` are repeatable (pass multiple times).

**Precedence**: explicit `init()` parameter > CLI flag > environment variable > hardcoded default.

### `server_url`

URL of the Smello server and the activation signal. Without a URL, `init()` does nothing. No patching, no background threads, no side effects.

Set via env var: `SMELLO_URL=http://smello:5110`.

### `debug`

Enable debug logging to stderr. When active, Smello logs its resolved configuration (with provenance showing where each value came from), which libraries were patched, every capture decision, and transport activity. This is the first thing to turn on when Smello appears to be running but you don't see events in the dashboard.

Set via env var: `SMELLO_DEBUG=1`.

You can also configure the `"smello"` Python logger manually for more control — see [Logging](#logging) below.

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

Minimum log level to capture. Default: `30` (WARNING). Accepts an integer or a level name (case-insensitive): `DEBUG` (10), `INFO` (20), `WARNING` (30), `ERROR` (40), `CRITICAL` (50).

Set via env var: `SMELLO_LOG_LEVEL=INFO` or `SMELLO_LOG_LEVEL=20`.

### `ignore_loggers`

List of logger names to exclude from capture. Records from the named loggers and their children are silently dropped. Useful for suppressing noisy framework loggers like `uvicorn.access` that duplicate information already captured by the incoming HTTP middleware.

Set via env var: `SMELLO_IGNORE_LOGGERS=uvicorn.access,uvicorn.error` (comma-separated).

Matching is hierarchical: `ignore_loggers=["uvicorn"]` suppresses `uvicorn`, `uvicorn.access`, `uvicorn.error`, etc. It does **not** match unrelated loggers that happen to share a prefix (e.g., `"uv"` does not suppress `"uvicorn"`).

!!! note "log_level is a capture filter, not a logger override"
    `log_level` controls which records Smello keeps *after* they pass through Python's normal logging pipeline. It cannot capture records that the application's loggers have already filtered out. For example, if your root logger is at WARNING (the default) and you set `log_level=10`, Smello still won't see DEBUG or INFO records. Python's `Logger.debug()` discards them before Smello's hook runs.

    To capture DEBUG-level logs, configure your application's logging level accordingly:

    ```python
    import logging
    logging.basicConfig(level=logging.DEBUG)
    ```

### `app`

Application name tag. Tags every captured event so you can filter by app on the dashboard or via the API query parameter `?app=payment-service`. Useful when multiple services share a single Smello server.

Set via env var: `SMELLO_APP=payment-service`.

### `session`

Session ID tag. Tags events with a debugging session identifier so you can isolate a specific investigation from everything else. Use a mnemonic name (e.g. `debug-payment-flow`) or a UUID.

Set via env var: `SMELLO_SESSION=debug-payment-flow`.

## Environment-only configuration

For zero code changes, use `smello run` and control everything via environment variables:

```bash
export SMELLO_URL=http://localhost:5110
export SMELLO_IGNORE_HOSTS=localhost,internal.svc
export SMELLO_CAPTURE_LOGS=true
export SMELLO_LOG_LEVEL=20

smello run my_app.py
```

Or equivalently, pass the options as CLI flags:

```bash
smello run --ignore-host localhost --capture-logs --log-level INFO my_app.py
```

Without `SMELLO_URL`, Smello is inactive: no patching, no side effects. Useful for Docker Compose, CI, and `.env` files.

## Debugging sessions

Tag events with `--app` and `--session` to isolate a debugging run:

```bash
smello run --app payment-service --session debug-payment-flow python scripts/checkout.py
curl 'http://localhost:5110/api/events?app=payment-service&session=debug-payment-flow'
```

Multiple services can share the same session to see the full picture in one filtered view.

## Body capture limits

Smello caps captured request and response bodies at **1 MB**. When a body exceeds the limit, the request is still captured (method, URL, headers, status code, timing), but the body field is omitted.

For streaming responses (common with LLM APIs), Smello accumulates chunks in memory as they pass through. Once the 1 MB threshold is crossed, accumulated data is discarded and no further chunks are stored. Your application receives all bytes normally; only the captured copy is affected.

The limit is not configurable. It prevents memory pressure when large downloads or file transfers pass through an instrumented application.

## Flushing and shutdown

Smello sends captures in a background thread so it never blocks your application. This means your process may exit before all captures reach the server, especially in short-lived scripts or CLI tools.

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

Smello uses Python's standard `logging` module for its own diagnostics. By default it is silent. A `NullHandler` is attached to the `smello` logger so no output is produced unless you opt in.

The quickest way to see debug output is `debug=True`:

```python
smello.init(server_url="http://localhost:5110", debug=True)
```

Or via environment: `SMELLO_DEBUG=1`. Or via CLI: `smello run --debug ...`.

This attaches a `StreamHandler(stderr)` to the `"smello"` logger at DEBUG level. Example output:

```
smello: resolved config:
  server_url = http://localhost:5110 (default)
  debug = True (--debug)
  capture_all = True (default)
  capture_hosts = [] (default)
  ignore_hosts = [] (default)
  redact_headers = ['authorization', 'x-api-key', 'x-goog-api-key'] (default)
  redact_query_params = [] (default)
  capture_exceptions = True (default)
  capture_logs = False (default)
  log_level = 30 (default)
  ignore_loggers = [] (default)
  app =  (default)
  session =  (default)
smello: patched requests.Session.send
smello: patched httpx.Client and httpx.AsyncClient
smello: skipped grpc patch (not installed)
smello: connected to http://localhost:5110 (200)
smello: captured GET https://api.example.com/users via requests (200)
smello: sent /api/capture/http (201)
```

Each field shows its value and where it came from: `(--debug)` for a CLI flag, `(SMELLO_URL)` for a user-set env var, `(param)` for an `init()` parameter, or `(default)` for the hardcoded default.

For more control, configure the `"smello"` logger directly:

```python
import logging
logging.getLogger("smello").setLevel(logging.DEBUG)
logging.getLogger("smello").addHandler(logging.FileHandler("smello-debug.log"))
```

You can also route Smello logs to a file or integrate them with your application's existing logging configuration. Just configure the `"smello"` logger however you like.

!!! note "Smello diagnostics vs. log capture"
    These are two separate things. **Smello diagnostics** (`logging.getLogger("smello")`) controls Smello's own debug output. **Log capture** (`capture_logs=True`) captures your application's log records and sends them to the dashboard. Smello never captures its own loggers to avoid recursion.

## Client CLI: `smello run`

`smello run` wraps any Python program and activates Smello in the wrapped process without modifying its source. It works by prepending a bootstrap directory to `PYTHONPATH` and executing your command, so subprocess instrumentation propagates automatically. Wrapping `gunicorn` patches its workers too.

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

Each flag maps 1:1 to a `SMELLO_*` environment variable — see the [Parameters](#parameters) table for the full list. The flag wins when both are set. `smello run` also defaults `server_url` to `http://localhost:5110` when neither `--server` nor `SMELLO_URL` is set.

CLI-specific behavior worth knowing:

- **`.py` script detection**: if the wrapped command ends in `.py` or `.pyw`, `smello run` prepends `sys.executable` so the script runs even without an executable bit or shebang. Same UX as `coverage run script.py`.
- **`--capture-host` implies `--no-capture-all`**: passing `--capture-host` without an explicit `--capture-all` switches the wrapper into "only these hosts" mode. Pass `--capture-all` explicitly if you want both an allowlist and the catch-all.
- **`smello.init()` is idempotent**: wrapping a program that already calls `smello.init()` is safe. The wrapper's bootstrap init runs first, then the program's `init()` updates the live config in place without re-applying patches (no double-capture).
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
