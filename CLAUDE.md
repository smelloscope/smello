# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install all workspace packages
uv sync

# Run the server (default: http://localhost:5110)
uv run smello-server run

# Run all tests
uv run pytest

# Run tests by scope
uv run pytest server/tests/          # server unit tests
uv run pytest clients/python/tests/  # client SDK tests
uv run pytest tests/test_e2e/        # end-to-end tests

# Run a single test
uv run pytest server/tests/test_api.py::test_capture_returns_201 -v

# Type checking
uv run ty check server/src clients/python/src

# Linting (runs automatically via pre-commit hooks)
uv run ruff check .
uv run ruff format .

# Bump versions (patch, minor, or major)
just bump-client patch   # smello client SDK
just bump-server minor   # smello-server

# Frontend (React SPA)
cd frontend && npm install      # install dependencies
cd frontend && npm run dev      # dev server on http://localhost:5111 (proxies /api to :5110)
cd frontend && npm run build    # production build to frontend/dist/
cd frontend && npm test         # run Vitest tests
cd frontend && npx orval        # regenerate API types from OpenAPI spec
just frontend-bundle            # build frontend + copy into server package for wheel
```

## Architecture

This is a **uv workspace monorepo** with two packages plus a React frontend:

- **`clients/python/` (smello)** — Client SDK with zero dependencies. Monkey-patches `requests.Session.send`, `httpx.Client.send`/`AsyncClient.send`, `grpc.insecure_channel`/`grpc.secure_channel`, and `botocore.httpsession.URLLib3Session.send` to intercept outgoing traffic. Serializes request/response pairs and sends them to the server via a background thread using `urllib` (to avoid triggering its own patches).

- **`server/` (smello-server)** — FastAPI app with Tortoise ORM + SQLite. Receives captured data at `POST /api/capture`, stores it, and serves a JSON API (`/api/*`). When `SMELLO_FRONTEND_DIR` points to a directory with built React assets, also serves the web dashboard.

- **`frontend/`** — React SPA built with Vite, MUI, TanStack Query, and jotai. API types and hooks are generated from the FastAPI OpenAPI spec using Orval. In development, Vite on port 5111 proxies `/api/*` to FastAPI on port 5110. In Docker, the frontend is pre-built and served by FastAPI directly.

**Data flow:** Patched library (requests/httpx/grpc) → `smello.capture.serialize_request_response` → background queue (`smello.transport`) → `POST /api/capture` → Tortoise ORM → SQLite → JSON API → React SPA.

## Key Patterns

- **Server routes** are in `routes/api.py` (JSON API with Pydantic response models).
- **Frontend uses TanStack Query** for data fetching with 3-second polling interval (replaces HTMX polling). Orval generates typed hooks from the OpenAPI spec.
- **Frontend state**: jotai atoms for filter state and selected request ID (synced to URL hash for deep linking).
- **MUI components** throughout: Table, Chip, Select, List, Paper, etc. `react18-json-view` for JSON rendering with a `customizeNode` callback for value annotations.
- **Dark theme is manual, not MUI's built-in dark mode.** The app uses MUI's default light theme. Dark surfaces (toolbar, sidebar, dialogs) use custom `dark.*` tokens from `theme.ts` (e.g., `dark.textPrimary`, `dark.divider`). Do NOT use MUI palette tokens like `text.primary` or `divider` on dark surfaces — they resolve to light-theme colors and will be invisible. The `mono` font stack is also exported from `theme.ts`.
- **JSON value annotations** (`frontend/src/annotations/`): Recognizes patterns like Unix timestamps in JSON bodies and shows tooltip icons. To add a new annotator, create a detector function and register it in `registry.ts`. See `frontend/src/annotations/README.md`.
- **SPA serving**: The PyPI wheel ships pre-built frontend assets in `_frontend/`. `SMELLO_FRONTEND_DIR` env var overrides the bundled path (used in Docker). Precedence: env var > bundled `_frontend/` > API-only mode.
- **Client SDK has no dependencies**: Transport uses `urllib.request` directly to avoid patching recursion. The server's own hostname is auto-added to `ignore_hosts`.
- **Server tests** use `FastAPI.TestClient` with a fresh SQLite DB per test (see `server/tests/conftest.py`). Tortoise ORM global context is reset between tests via `_reset_tortoise_global_context()`.
- **E2E tests** spin up a real uvicorn server and a mock HTTP target, then verify the full capture pipeline via the API.
- **Three README files** must stay in sync: `README.md` (root), `clients/python/README.md` (PyPI page for smello), and `server/README.md` (PyPI page for smello-server). Update all three after significant changes.
- **Changelogs**: Each package has its own `CHANGELOG.md` — `server/CHANGELOG.md` and `clients/python/CHANGELOG.md`. Follow [Keep a Changelog](https://keepachangelog.com/) format. **Before committing**, review whether the changes are user-facing or changelog-worthy. If so, update the `[Unreleased]` section in the relevant changelog as a separate step before creating the commit. Bumping versions moves `[Unreleased]` entries to a versioned section automatically via bump-my-version.
- **Documentation site** (`docs/`): After significant changes to client or server logic, update the relevant pages (`docs/getting-started.md`, `docs/configuration.md`, `docs/api.md`).

## Screenshots

The landing page hero image (`docs/assets/screenshot.png`) is generated automatically.
To regenerate after UI changes:

```bash
# Prerequisites: smello-server on :5110, frontend dev server on :5111
cd scripts && npm install   # one-time

# Full pipeline: clear data → run demo → capture → mockup
node scripts/demo-mockup.mjs
```

The screenshot uses a transparent background so it blends into the landing page gradient.
See `scripts/README.md` for all options (dark mode, custom viewport, custom demo script).

You can also use the library directly from Node.js:

```js
import { generateMockup } from "./scripts/lib/mockup.mjs";
await generateMockup({ url: "http://localhost:5111", output: "out.png" });
```

## Brand Color Palette

Derived from the Smello logo. Use these colors for highlights, accents, and UI elements.

| Name         | Hex       | Usage                                        |
|--------------|-----------|----------------------------------------------|
| Dark Surface | `#2A2A2E` | Primary dark — toolbar, sidebar background   |
| Amber        | `#FFA600` | Primary accent — logo, highlights, active states |
| Light Amber  | `#FFB833` | Secondary accent — hover states, badges      |
| Pale Amber   | `#FFD480` | Tertiary accent — light highlights, muted    |
