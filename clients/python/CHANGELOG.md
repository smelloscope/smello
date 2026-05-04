# Changelog

All notable changes to **smello** (Python client SDK) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.9.0] - 2026-05-04

### Added

- **Exception capture**: Hook `sys.excepthook` and `threading.excepthook` to capture unhandled exceptions with full tracebacks, stack frames, and source context. Enabled by default (`capture_exceptions=True`). Events are flushed synchronously before the process exits.
- **Frame source snippets**: Each captured exception frame now includes up to 5 lines of source code before and after the failing line (`pre_context`/`post_context`), so you can see the surrounding code on the dashboard without opening the file. Synthetic filenames (`<frozen ...>`, `<string>`) and unreadable sources gracefully fall back to empty lists.
- **Log capture**: Hook `logging.Logger.callHandlers` to capture Python log records at or above a configurable level. Opt-in via `capture_logs=True` and `log_level` (default: WARNING). Smello's own loggers and `urllib3` are automatically excluded to prevent recursion.
- **New `init()` parameters**: `capture_exceptions` (bool, default `True`), `capture_logs` (bool, default `False`), `log_level` (int, default `30`/WARNING).
- **New environment variables**: `SMELLO_CAPTURE_EXCEPTIONS`, `SMELLO_CAPTURE_LOGS`, `SMELLO_LOG_LEVEL`.
- **New `smello run` flags** for the new options: `--capture-exceptions` / `--no-capture-exceptions`, `--capture-logs` / `--no-capture-logs`, and `--log-level LEVEL`. Each maps 1:1 to its `SMELLO_*` env var, keeping the wrapper feature-complete with the in-code `init()` API.

### Changed

- **Typed transport endpoints**: Patches now post to typed server endpoints — HTTP captures go to `/api/capture/http`, logs to `/api/capture/log`, and exceptions to `/api/capture/exception`. Previous releases posted HTTP captures to `/api/capture`. Requires `smello-server` with the typed-endpoint release.
- **Internal transport API**: `transport.send()` is replaced with `transport.send_http()`, `transport.send_log()`, and `transport.send_exception()`. Anyone wrapping the transport directly (rather than going through `smello.init()`) needs to update their imports.

## [0.8.0] - 2026-05-02

### Changed

- `smello.init()` is now idempotent. The first call applies the monkey-patches; subsequent calls update the live `SmelloConfig` in place so new args (filtering, redaction, server URL) take effect immediately without re-wrapping already patched methods. Previously, calling `init()` twice nested the patches, which would double-capture every request. This makes `smello run` safe to use on programs that also call `smello.init()` themselves.

### Added

- **`smello run` CLI**: Wrap any Python program to capture its HTTP traffic without modifying the source. `smello run my_app.py` runs `.py` files with the current Python (no chmod or shebang needed); `smello run uvicorn app:app` works with console scripts. Use `--` to disambiguate when wrapped command flags would conflict with smello's. Subprocess instrumentation propagates automatically through PYTHONPATH inheritance, so wrapping `gunicorn` patches its workers too. CLI flags map 1:1 to the existing `SMELLO_*` env vars (`--server`, `--capture-host`, `--ignore-host`, `--capture-all`/`--no-capture-all`, `--redact-header`, `--redact-query-param`). Passing `--capture-host` without an explicit `--capture-all` switches the wrapper into "only these hosts" mode, matching the flag's "Capture only this host" help text. See `examples/python/wrapper_demo.py` for a runnable example.

## [0.7.0] - 2026-04-07

### Added

- **aiohttp support**: Instrument `aiohttp.ClientSession` via TraceConfig signals to capture async HTTP traffic. Handles merged headers, base_url resolution, redirects, streaming, and `raise_for_status` by construction.

## [0.6.1] - 2026-03-22

## [0.6.0] - 2026-03-16

### Added

- **botocore/boto3 support**: Patch `botocore.httpsession.URLLib3Session.send()` to capture AWS SDK traffic. boto3 uses urllib3 directly, bypassing requests and httpx, so it needs its own patch.

### Fixed

- Binary response bodies no longer show as garbled text. Patches now pass raw bytes to the serializer, which renders non-UTF-8 content as `[binary: N bytes]`.

## [0.5.0] - 2026-03-11

### Added

- `redact_query_params` parameter and `SMELLO_REDACT_QUERY_PARAMS` env var to redact query string values (e.g. `?api_key=sk-...` → `?api_key=[REDACTED]`).

## [0.4.0] - 2026-02-22

### Changed

- **BREAKING**: Remove `enabled` parameter and `SMELLO_ENABLED` env var. The server URL is now the activation signal — `init()` does nothing unless `server_url` is passed or `SMELLO_URL` is set.
- **BREAKING**: Remove default server URL. `server_url` must be configured explicitly.

## [0.3.1] - 2026-02-20

## [0.3.0] - 2026-02-20

### Added

- gRPC interception support for unary-unary calls via `grpc.insecure_channel()` and `grpc.secure_channel()`.
- Environment variable configuration: all `init()` parameters now fall back to `SMELLO_*` env vars when not passed explicitly (`SMELLO_ENABLED`, `SMELLO_URL`, `SMELLO_CAPTURE_ALL`, `SMELLO_CAPTURE_HOSTS`, `SMELLO_IGNORE_HOSTS`, `SMELLO_REDACT_HEADERS`).

### Fixed

- Fix gRPC capture for Google Cloud libraries: base64-encode binary metadata (keys ending with `-bin`) and unwrap proto-plus wrappers via the `_pb` attribute.

### Changed

- All `init()` parameter defaults changed from hardcoded values to `None` sentinels. Existing code that calls `smello.init()` without arguments is unaffected — the same hardcoded defaults apply when no env vars are set.
- Use `repr()` as a generic JSON serialization fallback in transport so non-serializable types (bytes, custom objects) never crash the capture pipeline.

## [0.2.0] - 2026-02-20

### Added

- `flush()` and `shutdown()` functions to drain the capture queue before exit.
- Automatic `atexit` hook to flush pending captures on interpreter shutdown.
- Logging via the standard `logging` module (`smello.*` loggers).

### Changed

- Silenced exceptions in patches now log at DEBUG level instead of being swallowed.
- Full capture queue now logs a WARNING instead of dropping silently.
- Failed server sends now log a WARNING with the error details.

## [0.1.1] - 2026-02-19

### Changed

- Change default server port from 8080 to 5110.
- Update repository references from `imankulov/smello` to `smelloscope/smello`.

## [0.1.0] - 2026-02-16

- Initial release.
