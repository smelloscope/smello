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
```

## Architecture

This is a **uv workspace monorepo** with two packages:

- **`clients/python/` (smello)** — Client SDK with zero dependencies. Monkey-patches `requests.Session.send` and `httpx.Client.send`/`AsyncClient.send` to intercept outgoing HTTP traffic. Serializes request/response pairs and sends them to the server via a background thread using `urllib` (to avoid triggering its own patches).

- **`server/` (smello-server)** — FastAPI app with Tortoise ORM + SQLite. Receives captured data at `POST /api/capture`, stores it, and serves both a JSON API (`/api/*`) and a web dashboard (`/`) with Jinja2 templates + HTMX.

**Data flow:** Patched HTTP library → `smello.capture.serialize_request_response` → background queue (`smello.transport`) → `POST /api/capture` → Tortoise ORM → SQLite → Web UI / JSON API.

## Key Patterns

- **Server routes are split**: `routes/api.py` (JSON API with Pydantic response models) and `routes/web.py` (HTML, excluded from OpenAPI schema via `include_in_schema=False`).
- **Web UI uses HTMX**: Gmail-style two-column layout. List panel polls `GET /?_partial=list` every 3s; clicking a row loads `GET /requests/{id}/partial` into the detail panel. Detail partial is shared between the split view and the full-page detail route via `{% include %}`.
- **Client SDK has no dependencies**: Transport uses `urllib.request` directly to avoid patching recursion. The server's own hostname is auto-added to `ignore_hosts`.
- **Server tests** use `FastAPI.TestClient` with a fresh SQLite DB per test (see `server/tests/conftest.py`). Tortoise ORM global context is reset between tests via `_reset_tortoise_global_context()`.
- **E2E tests** spin up a real uvicorn server and a mock HTTP target, then verify the full capture-to-rendering pipeline.
- **Three README files** must stay in sync: `README.md` (root), `clients/python/README.md` (PyPI page for smello), and `server/README.md` (PyPI page for smello-server). After significant changes, review and update all three.
