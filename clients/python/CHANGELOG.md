# Changelog

All notable changes to **smello** (Python client SDK) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
