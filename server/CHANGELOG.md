# Changelog

All notable changes to **smello-server** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.6.0] - 2026-05-04

### Added

- **Typed event payloads**: `GET /api/events/{id}` now returns `data` as a Pydantic-discriminated union (`HttpEventData | LogEventData | ExceptionEventData`) instead of an opaque object. The OpenAPI schema exposes the discriminator so frontends can generate strongly-typed clients (the bundled dashboard now uses `openapi-typescript`). Old DB rows written before this change are hydrated transparently on read.
- **HTTP meta promoted**: `python_version` and `smello_version` are now stored alongside `library` in the HTTP event payload (previously dropped at write time).
- **`smello-server openapi-export`**: New CLI command that writes the FastAPI OpenAPI schema to a JSON file. Used by the frontend's type-generation step and the matching `just openapi-export` recipe.
- **Unified event model**: Replace the HTTP-only `CapturedRequest` model with a unified `CapturedEvent` model that supports multiple event types — HTTP requests, log records, and exceptions — in a single timeline.
- **Typed capture endpoints**: New `POST /api/capture/http`, `POST /api/capture/log`, and `POST /api/capture/exception` endpoints, each with a strict Pydantic input schema. The original HTTP-only `POST /api/capture` is preserved (deprecated) for older client wheels.
- **Log event capture**: New `log` event type stores Python log records with level, logger name, message, source location, and extra attributes.
- **Exception event capture**: New `exception` event type stores unhandled exceptions with type, message, full traceback text, and structured stack frames.
- **`/api/events` endpoint**: New unified timeline endpoint returning all event types sorted by timestamp. Supports filtering by `event_type`, `host`, `method`, `status`, and full-text `search`.
- **`/api/events/{id}` endpoint**: Returns full event detail with type-specific data in a `data` JSON field.
- **Event type filter in meta**: `GET /api/meta` now returns `event_types` alongside `hosts` and `methods`.
- **`DELETE /api/events`**: Clear all events (all types).
- **`services/` layer**: Persistence and queries live in `services/capture.py` (writes) and `services/events.py` (reads). Routes are thin wrappers, so behavior can be tested directly against the service functions without an HTTP roundtrip.
- **Open-in-editor icon in exception frames**: Each captured exception frame in the dashboard now shows a small VS Code icon next to `File:Line`. Clicking it opens the file at that line in VS Code (or any VS Code-based editor like Cursor) via the `vscode://file/...` URL scheme.
- **Expandable source snippets in exception frames**: Click a frame row to expand a syntax-highlighted Python snippet showing the lines around the failing line, with the failing line highlighted. Powered by `pre_context`/`post_context` fields captured by the client SDK.

### Changed

- **Data model**: Events are stored in a single `captured_events` table with `event_type`, `summary`, and `data` (JSON) columns, replacing the previous multi-column `captured_requests` table.
- **Dashboard**: The event list now shows HTTP requests, logs, and exceptions in a unified timeline with distinct visual styles — method badges for HTTP, level badges for logs, and traceback previews for exceptions. A new "All types" dropdown filters by event type.

### Deprecated

- **`POST /api/capture`**: The original HTTP-only capture endpoint is now marked `deprecated` in the OpenAPI spec. It still accepts the same payload shape so older client wheels keep working (they only ever posted HTTP captures here), but will be removed in a future release. Use the typed endpoints (`/api/capture/http`, `/api/capture/log`, `/api/capture/exception`) instead.

### Removed

- **BREAKING**: Removed the `/api/requests`, `/api/requests/{id}`, and `DELETE /api/requests` endpoints. Use `/api/events?event_type=http`, `/api/events/{id}`, and `DELETE /api/events` instead. Detail responses now return HTTP fields nested under `data` (e.g. `data.method`, `data.request_headers`) rather than at the top level.

## [0.5.0] - 2026-04-07

### Added

- **Full-text search**: The search field now matches across URLs, hosts, methods, request/response headers, and request/response bodies — not just the URL.

## [0.4.3] - 2026-03-23

### Added

- **Startup banner**: Shows the server URL, a GitHub star link, and a link to discussions on startup.
- **Auto-open browser**: The dashboard opens in your browser automatically on start. Use `--no-open` to disable.

### Changed

- **CLI migrated to Typer**: Replaced argparse with Typer. The `run` subcommand is removed; use `smello-server [OPTIONS]` directly.

## [0.4.2] - 2026-03-23

### Added

- **Keyboard shortcuts**: Gmail/Linear-style hotkeys for the dashboard — j/k to navigate requests, / to search, h/b to toggle sections, c to copy body, ? to view all shortcuts.

## [0.4.1] - 2026-03-22

### Added

- **Resizable split view**: The divider between the request list and detail panel can now be dragged to resize. Layout is persisted to localStorage.

### Changed

- **Dark sidebar & toolbar**: Request list and top toolbar now use a dark surface (`#2A2A2E`) with light text, inspired by Bear's design. Method badges use bright colors on dark backgrounds for readability.
- **Streamlined header**: Removed the separate title bar ("Smello — HTTP Request Inspector"); the logo is now inlined into the filter bar.
- **Updated brand palette**: Replaced blue/navy colors with a dark surface + amber (`#FFA600`) palette across the app, docs, and landing page.

## [0.4.0] - 2026-03-16

### Added

- **XML body rendering**: Parse XML responses (common in AWS S3, STS, EC2, IAM) into a collapsible tree view, matching the existing JSON treatment.
- **Tree / Raw tabs** for JSON and XML bodies. Tree (default) shows an expandable tree; Raw shows syntax-highlighted source.

## [0.3.4] - 2026-03-11

### Added

- Annotate Unix timestamps (seconds and milliseconds) in JSON response bodies with a tooltip showing the human-readable date.

## [0.3.3] - 2026-03-05

### Improved

- Decode percent-encoded URL query strings in the request list and detail views (e.g. `page%5Bnumber%5D` → `page[number]`).
- Add collapsible "Query Parameters" table to the Request section in the detail view, showing parsed key-value pairs.

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
