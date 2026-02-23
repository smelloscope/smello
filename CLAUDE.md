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
```

## Architecture

This is a **uv workspace monorepo** with two packages plus a React frontend:

- **`clients/python/` (smello)** — Client SDK with zero dependencies. Monkey-patches `requests.Session.send`, `httpx.Client.send`/`AsyncClient.send`, and `grpc.insecure_channel`/`grpc.secure_channel` to intercept outgoing traffic. Serializes request/response pairs and sends them to the server via a background thread using `urllib` (to avoid triggering its own patches).

- **`server/` (smello-server)** — FastAPI app with Tortoise ORM + SQLite. Receives captured data at `POST /api/capture`, stores it, and serves a JSON API (`/api/*`). When `SMELLO_FRONTEND_DIR` points to a directory with built React assets, also serves the web dashboard.

- **`frontend/`** — React SPA built with Vite, MUI, TanStack Query, and jotai. API types and hooks are generated from the FastAPI OpenAPI spec using Orval. In development, Vite on port 5111 proxies `/api/*` to FastAPI on port 5110. In Docker, the frontend is pre-built and served by FastAPI directly.

**Data flow:** Patched library (requests/httpx/grpc) → `smello.capture.serialize_request_response` → background queue (`smello.transport`) → `POST /api/capture` → Tortoise ORM → SQLite → JSON API → React SPA.

## Key Patterns

- **Server routes** are in `routes/api.py` (JSON API with Pydantic response models).
- **Frontend uses TanStack Query** for data fetching with 3-second polling interval (replaces HTMX polling). Orval generates typed hooks from the OpenAPI spec.
- **Frontend state**: jotai atoms for filter state and selected request ID (synced to URL hash for deep linking).
- **MUI components** throughout: Table, Chip, Select, List, Paper, etc. `react18-json-view` for JSON rendering.
- **SPA serving**: `SMELLO_FRONTEND_DIR` env var tells FastAPI where to find built React assets. Set automatically in Docker. Missing = API-only mode.
- **Client SDK has no dependencies**: Transport uses `urllib.request` directly to avoid patching recursion. The server's own hostname is auto-added to `ignore_hosts`.
- **Server tests** use `FastAPI.TestClient` with a fresh SQLite DB per test (see `server/tests/conftest.py`). Tortoise ORM global context is reset between tests via `_reset_tortoise_global_context()`.
- **E2E tests** spin up a real uvicorn server and a mock HTTP target, then verify the full capture pipeline via the API.
- **Three README files** must stay in sync: `README.md` (root), `clients/python/README.md` (PyPI page for smello), and `server/README.md` (PyPI page for smello-server). Update all three after significant changes.
- **Changelogs**: Each package has its own `CHANGELOG.md` — `server/CHANGELOG.md` and `clients/python/CHANGELOG.md`. Follow [Keep a Changelog](https://keepachangelog.com/) format. Update the `[Unreleased]` section in every commit that introduces a user-facing or changelog-worthy change. Bumping versions moves `[Unreleased]` entries to a versioned section automatically via bump-my-version.
- **Documentation site** (`docs/`): After significant changes to client or server logic, update the relevant pages (`docs/getting-started.md`, `docs/configuration.md`, `docs/api.md`).
