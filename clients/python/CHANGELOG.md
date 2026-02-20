# Changelog

All notable changes to **smello** (Python client SDK) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
