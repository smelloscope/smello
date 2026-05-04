"""Fixtures for server tests."""

import pytest
import pytest_asyncio
import tortoise.context
from fastapi.testclient import TestClient
from smello_server.app import create_app
from tortoise import Tortoise


def _reset_tortoise_global_context():
    """Reset Tortoise ORM's global context so a new app can initialize."""
    tortoise.context._global_context = None


@pytest.fixture()
def client(tmp_path):
    """Create a TestClient with a fresh SQLite database."""
    _reset_tortoise_global_context()

    db_url = f"sqlite://{tmp_path / 'test.db'}"

    app = create_app(db_url=db_url)

    with TestClient(app) as tc:
        yield tc

    _reset_tortoise_global_context()


@pytest_asyncio.fixture()
async def services_db(tmp_path):
    """Initialize Tortoise against a fresh SQLite without spinning up FastAPI.

    Use this for service-level tests that talk to the persistence layer
    directly (no HTTP roundtrip).
    """
    _reset_tortoise_global_context()
    db_url = f"sqlite://{tmp_path / 'services.db'}"
    await Tortoise.init(db_url=db_url, modules={"models": ["smello_server.models"]})
    await Tortoise.generate_schemas()
    try:
        yield
    finally:
        await Tortoise.close_connections()
        _reset_tortoise_global_context()


# --- Sample HTTP payloads (legacy polymorphic shape) ---


@pytest.fixture()
def sample_payload():
    """A reusable sample HTTP capture payload (legacy shape)."""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "duration_ms": 150,
        "request": {
            "method": "GET",
            "url": "https://api.example.com/v1/test",
            "headers": {"Content-Type": "application/json"},
            "body": None,
            "body_size": 0,
        },
        "response": {
            "status_code": 200,
            "headers": {"Content-Type": "application/json"},
            "body": '{"result": "success"}',
            "body_size": 21,
        },
        "meta": {
            "library": "requests",
            "python_version": "3.12.2",
            "smello_version": "0.1.0",
        },
    }


@pytest.fixture()
def make_payload():
    """Factory fixture for HTTP capture payloads (legacy shape)."""

    def _make(
        *, method="GET", url="https://api.example.com/test", status_code=200, **kwargs
    ):
        payload = {
            "id": None,
            "duration_ms": 100,
            "request": {
                "method": method,
                "url": url,
                "headers": {"Content-Type": "application/json"},
                "body": None,
                "body_size": 0,
            },
            "response": {
                "status_code": status_code,
                "headers": {"Content-Type": "application/json"},
                "body": '{"ok": true}',
                "body_size": 12,
            },
            "meta": {"library": "requests"},
        }
        payload.update(kwargs)
        return payload

    return _make


# --- Typed payloads (new endpoints) ---


@pytest.fixture()
def http_payload(sample_payload):
    """HTTP payload for the typed `/api/capture/http` endpoint.

    Same shape `sample_payload` already uses — both the typed `/api/capture/http`
    endpoint and the deprecated HTTP-only `/api/capture` accept it.
    """
    return sample_payload


@pytest.fixture()
def log_payload():
    """Log payload for the typed `/api/capture/log` endpoint."""
    return {
        "data": {
            "level": "WARNING",
            "logger_name": "myapp.auth",
            "message": "Token expired for user 42",
            "pathname": "/app/auth.py",
            "lineno": 87,
            "func_name": "validate_token",
        }
    }


@pytest.fixture()
def exception_payload():
    """Exception payload for the typed `/api/capture/exception` endpoint."""
    return {
        "data": {
            "exc_type": "ValueError",
            "exc_value": "invalid literal for int() with base 10: 'abc'",
            "exc_module": "builtins",
            "traceback_text": (
                "Traceback (most recent call last):\n"
                '  File "app.py", line 42, in main\n'
                "    x = int(user_input)\n"
                "ValueError: invalid literal for int() with base 10: 'abc'\n"
            ),
            "frames": [
                {
                    "filename": "app.py",
                    "lineno": 42,
                    "function": "main",
                    "context_line": "    x = int(user_input)",
                }
            ],
        }
    }
