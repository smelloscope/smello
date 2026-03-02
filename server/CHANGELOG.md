# Changelog

All notable changes to **smello-server** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.3.2] - 2026-03-02

### Improved

- Redesign dashboard request list: show URL path as primary text with host as secondary, making requests scannable at a glance.
- Add color-coded HTTP method badges (GET blue, POST green, PUT orange, DELETE red, PATCH purple).
- Smart gRPC URL display: extract `Service/Method` from fully-qualified gRPC paths.
- Move status badges to right-aligned column for consistent visual alignment.
- Show duration in human-friendly format (`1.7s` instead of `1700ms`) with warning highlight for slow requests (>2s).
- Improve detail panel header: separate host from path, show duration and library as chips.
- Add directional icons to Request/Response sections.
- Reorder filter bar: method and host selects on the left, search field fills remaining space.
- Replace floating-label selects with compact inline-placeholder style.
- Regenerate landing page screenshot.

## [0.3.1] - 2026-03-02

### Improved

- Show database path on startup and in `--help` output (default: `~/.smello/smello.db`).
- Fix `--host` default documented as `127.0.0.1` — actual default is `0.0.0.0`.

## [0.3.0] - 2026-03-02

### Added

- Bundle pre-built React frontend into the PyPI wheel. `pip install smello-server && smello-server run` now serves the full web dashboard — Docker is no longer required.

## [0.2.2] - 2026-02-27

## [0.2.1] - 2026-02-23

## [0.2.0] - 2026-02-23

### Added

- `GET /api/meta` endpoint returning distinct hosts and methods for filter dropdowns.
- React SPA frontend (MUI, TanStack Query, jotai) replacing Jinja2/HTMX server-side rendering.
- `SMELLO_FRONTEND_DIR` env var to serve pre-built frontend assets from FastAPI.
- Multi-stage Dockerfile building both frontend and server.

### Removed

- Jinja2 templates, HTMX, and all server-side rendered web routes.
- `jinja2` dependency.

## [0.1.2] - 2026-02-20

## [0.1.1] - 2025-01-01

### Fixed

- Fix bump recipes: add `--frozen` to prevent `uv.lock` modification.

## [0.1.0] - 2025-01-01

- Initial release.
