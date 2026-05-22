"""Tests for smello.integrations.fastapi — SmelloMiddleware."""

from unittest.mock import patch

import pytest

fastapi = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")

from fastapi import FastAPI  # noqa: E402
from smello.config import SmelloConfig  # noqa: E402
from smello.integrations.fastapi import SmelloMiddleware  # noqa: E402
from starlette.applications import Starlette  # noqa: E402
from starlette.routing import WebSocketRoute  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402
from starlette.websockets import WebSocket  # noqa: E402


@pytest.fixture()
def config():
    return SmelloConfig(
        server_url="http://smello:5110",
        redact_headers=["authorization"],
    )


@pytest.fixture()
def captured(config):
    """Patch smello._config and collect send_http_incoming payloads."""
    payloads: list[dict] = []
    with (
        patch("smello._config", config),
        patch(
            "smello.integrations.fastapi.send_http_incoming",
            side_effect=payloads.append,
        ),
    ):
        yield payloads


def _make_app():
    app = FastAPI()
    app.add_middleware(SmelloMiddleware)

    @app.get("/hello")
    def hello():
        return {"message": "world"}

    @app.post("/echo")
    async def echo(body: dict):
        return body

    @app.get("/error")
    def error():
        raise ValueError("boom")

    return app


@pytest.fixture()
def app():
    return _make_app()


@pytest.fixture()
def client(app):
    with TestClient(app, raise_server_exceptions=False) as tc:
        yield tc


def test_captures_basic_get(captured, client):
    resp = client.get("/hello")
    assert resp.status_code == 200

    assert len(captured) == 1
    payload = captured[0]
    assert payload["request"]["method"] == "GET"
    assert payload["request"]["path"] == "/hello"
    assert payload["response"]["status_code"] == 200
    assert payload["duration_ms"] >= 0
    assert payload["meta"]["framework"] == "fastapi"


def test_url_uses_host_header_over_server(captured, client):
    client.get("/hello")
    payload = captured[0]
    assert "testserver" in payload["request"]["url"]


def test_payload_includes_timestamp(captured, client):
    client.get("/hello")
    payload = captured[0]
    assert "timestamp" in payload
    assert "T" in payload["timestamp"]


def test_captures_request_body(captured, client):
    resp = client.post("/echo", json={"key": "value"})
    assert resp.status_code == 200

    payload = captured[0]
    assert '"key"' in payload["request"]["body"]
    assert payload["request"]["body_size"] > 0


def test_captures_response_body(captured, client):
    client.get("/hello")
    payload = captured[0]
    assert '"message"' in payload["response"]["body"]
    assert payload["response"]["body_size"] > 0


def test_redacts_query_params(captured, config, client):
    config.redact_query_params = ["token"]
    client.get("/hello?token=secret&page=1")
    payload = captured[0]
    assert "secret" not in payload["request"]["url"]
    assert "REDACTED" in payload["request"]["url"]
    assert "page=1" in payload["request"]["url"]


def test_redacts_headers(captured, client):
    client.get("/hello", headers={"Authorization": "Bearer secret123"})
    payload = captured[0]
    auth_values = [
        v
        for k, v in payload["request"]["headers"].items()
        if k.lower() == "authorization"
    ]
    assert all(v == "[REDACTED]" for v in auth_values)


def test_captures_exception_info(captured, client):
    exception_calls: list[tuple] = []
    with patch(
        "smello.integrations.fastapi.capture_exception",
        side_effect=lambda *args: exception_calls.append(args),
    ):
        resp = client.get("/error")
    assert resp.status_code == 500

    exc_payloads = [p for p in captured if p["meta"]["exc_type"] is not None]
    assert len(exc_payloads) == 1
    payload = exc_payloads[0]
    assert payload["meta"]["exc_type"] == "ValueError"
    assert payload["meta"]["exc_value"] == "boom"
    assert payload["response"]["status_code"] == 500

    assert len(exception_calls) == 1
    exc_type, exc_value, exc_tb = exception_calls[0]
    assert exc_type is ValueError
    assert str(exc_value) == "boom"
    assert exc_tb is not None


def test_no_capture_when_config_is_none(client):
    """When smello is not initialized, middleware is a no-op."""
    payloads: list[dict] = []
    with (
        patch("smello._config", None),
        patch(
            "smello.integrations.fastapi.send_http_incoming",
            side_effect=payloads.append,
        ),
    ):
        resp = client.get("/hello")
        assert resp.status_code == 200
        assert len(payloads) == 0


def test_websocket_passthrough(captured):
    """Non-HTTP scopes pass through without capture."""

    async def ws_endpoint(ws: WebSocket):
        await ws.accept()
        await ws.send_text("hi")
        await ws.close()

    app = Starlette(routes=[WebSocketRoute("/ws", ws_endpoint)])
    app.add_middleware(SmelloMiddleware)

    with TestClient(app) as tc:
        with tc.websocket_connect("/ws") as ws:
            data = ws.receive_text()
            assert data == "hi"

    assert len(captured) == 0


# --- ignore_paths ---


def _make_app_with_ignore_paths(ignore_paths):
    app = FastAPI()
    app.add_middleware(SmelloMiddleware, ignore_paths=ignore_paths)

    @app.get("/hello")
    def hello():
        return {"message": "world"}

    @app.get("/docs/extra")
    def docs_extra():
        return {"docs": True}

    return app


def test_ignore_paths_skips_capture(captured):
    app = _make_app_with_ignore_paths(["/docs"])
    with TestClient(app) as tc:
        resp = tc.get("/docs/extra")
        assert resp.status_code == 200
    assert len(captured) == 0


def test_ignore_paths_prefix_match(captured):
    app = _make_app_with_ignore_paths(["/docs"])
    with TestClient(app) as tc:
        tc.get("/docs/extra")
    assert len(captured) == 0


def test_ignore_paths_does_not_affect_other_routes(captured):
    app = _make_app_with_ignore_paths(["/docs"])
    with TestClient(app) as tc:
        tc.get("/hello")
    assert len(captured) == 1
    assert captured[0]["request"]["path"] == "/hello"


def test_ignore_paths_empty_list(captured):
    app = _make_app_with_ignore_paths([])
    with TestClient(app) as tc:
        tc.get("/hello")
    assert len(captured) == 1
