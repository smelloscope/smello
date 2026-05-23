"""Tests for smello.integrations.django — SmelloMiddleware."""

from unittest.mock import patch

import pytest

django = pytest.importorskip("django")

from django.conf import settings  # noqa: E402

if not settings.configured:
    settings.configure(
        ALLOWED_HOSTS=["*"],
        SECRET_KEY="test-secret",
    )
    import django as dj

    dj.setup()

from django.http import HttpResponse, JsonResponse, StreamingHttpResponse  # noqa: E402
from django.test import RequestFactory  # noqa: E402
from smello.config import SmelloConfig  # noqa: E402
from smello.integrations.django import SmelloMiddleware  # noqa: E402


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
            "smello.integrations.django.send_http_incoming",
            side_effect=payloads.append,
        ),
    ):
        yield payloads


@pytest.fixture()
def factory():
    return RequestFactory()


def _default_get_response(request):
    return JsonResponse({"message": "world"})


def _make_middleware(get_response=None, ignore_paths=None):
    if get_response is None:
        get_response = _default_get_response

    if ignore_paths is not None:
        with patch.object(settings, "SMELLO_IGNORE_PATHS", ignore_paths, create=True):
            return SmelloMiddleware(get_response)
    return SmelloMiddleware(get_response)


def test_captures_basic_get(captured, factory):
    middleware = _make_middleware()
    resp = middleware(factory.get("/hello"))

    assert resp.status_code == 200
    assert len(captured) == 1
    payload = captured[0]
    assert payload["request"]["method"] == "GET"
    assert payload["request"]["path"] == "/hello"
    assert payload["response"]["status_code"] == 200
    assert payload["duration_ms"] >= 0
    assert payload["meta"]["framework"] == "django"


def test_payload_includes_timestamp(captured, factory):
    middleware = _make_middleware()
    middleware(factory.get("/hello"))
    payload = captured[0]
    assert "timestamp" in payload
    assert "T" in payload["timestamp"]


def test_captures_request_body(captured, factory):
    middleware = _make_middleware(
        lambda request: JsonResponse({"echo": True}),
    )
    middleware(
        factory.post("/echo", data=b'{"key": "value"}', content_type="application/json")
    )

    payload = captured[0]
    assert '"key"' in payload["request"]["body"]
    assert payload["request"]["body_size"] > 0


def test_captures_response_body(captured, factory):
    middleware = _make_middleware()
    middleware(factory.get("/hello"))
    payload = captured[0]
    assert '"message"' in payload["response"]["body"]
    assert payload["response"]["body_size"] > 0


def test_redacts_query_params(captured, config, factory):
    config.redact_query_params = ["token"]
    middleware = _make_middleware()
    middleware(factory.get("/hello?token=secret&page=1"))

    payload = captured[0]
    assert "secret" not in payload["request"]["url"]
    assert "REDACTED" in payload["request"]["url"]
    assert "page=1" in payload["request"]["url"]


def test_redacts_headers(captured, factory):
    middleware = _make_middleware()
    middleware(factory.get("/hello", HTTP_AUTHORIZATION="Bearer secret123"))

    payload = captured[0]
    auth_values = [
        v
        for k, v in payload["request"]["headers"].items()
        if k.lower() == "authorization"
    ]
    assert all(v == "[REDACTED]" for v in auth_values)


def test_captures_exception_info(captured, factory):
    exc = ValueError("boom")

    def get_response(request):
        return HttpResponse(status=500)

    exception_calls: list[tuple] = []
    middleware = _make_middleware(get_response)

    with patch(
        "smello.integrations.django.capture_exception",
        side_effect=lambda *args: exception_calls.append(args),
    ):
        request = factory.get("/error")
        middleware.process_exception(request, exc)
        resp = middleware(request)

    assert resp.status_code == 500
    assert len(captured) == 1
    payload = captured[0]
    assert payload["meta"]["exc_type"] == "ValueError"
    assert payload["meta"]["exc_value"] == "boom"

    assert len(exception_calls) == 1
    exc_type, exc_value, _exc_tb = exception_calls[0]
    assert exc_type is ValueError
    assert str(exc_value) == "boom"


def test_no_capture_when_config_is_none(factory):
    """When smello is not initialized, middleware is a no-op."""
    payloads: list[dict] = []
    with (
        patch("smello._config", None),
        patch(
            "smello.integrations.django.send_http_incoming",
            side_effect=payloads.append,
        ),
    ):
        middleware = _make_middleware()
        resp = middleware(factory.get("/hello"))
        assert resp.status_code == 200
        assert len(payloads) == 0


# --- ignore_paths ---


def test_ignore_paths_skips_capture(captured, factory):
    middleware = _make_middleware(ignore_paths=["/admin"])
    middleware(factory.get("/admin/login"))
    assert len(captured) == 0


def test_ignore_paths_prefix_match(captured, factory):
    middleware = _make_middleware(ignore_paths=["/admin"])
    middleware(factory.get("/admin/users/"))
    assert len(captured) == 0


def test_ignore_paths_does_not_affect_other_routes(captured, factory):
    middleware = _make_middleware(ignore_paths=["/admin"])
    middleware(factory.get("/hello"))
    assert len(captured) == 1
    assert captured[0]["request"]["path"] == "/hello"


def test_ignore_paths_empty_list(captured, factory):
    middleware = _make_middleware(ignore_paths=[])
    middleware(factory.get("/hello"))
    assert len(captured) == 1


# --- metadata ---


def test_url_includes_host(captured, factory):
    middleware = _make_middleware()
    middleware(factory.get("/hello"))
    payload = captured[0]
    assert "testserver" in payload["request"]["url"]


def test_route_pattern_extracted(captured, factory):
    from types import SimpleNamespace  # noqa: PLC0415

    middleware = _make_middleware()
    request = factory.get("/users/42")
    request.resolver_match = SimpleNamespace(route="users/<int:pk>")
    middleware(request)

    payload = captured[0]
    assert payload["meta"]["route"] == "users/<int:pk>"


def test_route_none_without_resolver_match(captured, factory):
    middleware = _make_middleware()
    middleware(factory.get("/hello"))
    payload = captured[0]
    assert payload["meta"]["route"] is None


def test_client_ip_extracted(captured, factory):
    middleware = _make_middleware()
    middleware(factory.get("/hello"))
    payload = captured[0]
    assert payload["meta"]["client_ip"] == "127.0.0.1"


# --- streaming ---


def test_streaming_response_body_placeholder(captured, factory):
    def get_response(request):
        return StreamingHttpResponse(iter([b"chunk1", b"chunk2"]))

    middleware = _make_middleware(get_response)
    middleware(factory.get("/stream"))

    assert len(captured) == 1
    payload = captured[0]
    assert payload["response"]["body"] == "[streaming]"
    assert payload["response"]["body_size"] == 0
    assert payload["response"]["status_code"] == 200


# --- large body ---


def test_large_request_body_skipped(captured, factory):
    from smello.integrations.django import MAX_BODY_CAPTURE  # noqa: PLC0415

    oversized = b"x" * (MAX_BODY_CAPTURE + 1)
    middleware = _make_middleware()
    middleware(
        factory.post("/upload", data=oversized, content_type="application/octet-stream")
    )

    assert len(captured) == 1
    payload = captured[0]
    assert payload["request"]["body"] is None
    assert payload["request"]["body_size"] == len(oversized)


# --- process_exception edge cases ---


def test_process_exception_skips_ignored_paths(captured, factory):
    exc = ValueError("boom")
    exception_calls: list[tuple] = []
    middleware = _make_middleware(ignore_paths=["/admin"])

    with patch(
        "smello.integrations.django.capture_exception",
        side_effect=lambda *args: exception_calls.append(args),
    ):
        request = factory.get("/admin/login")
        middleware.process_exception(request, exc)

    assert len(exception_calls) == 0
    assert not hasattr(request, "_smello_exc_type")


def test_process_exception_respects_capture_exceptions_false(captured, config, factory):
    config.capture_exceptions = False
    exc = ValueError("boom")
    exception_calls: list[tuple] = []
    middleware = _make_middleware()

    with patch(
        "smello.integrations.django.capture_exception",
        side_effect=lambda *args: exception_calls.append(args),
    ):
        request = factory.get("/error")
        middleware.process_exception(request, exc)

    assert len(exception_calls) == 0
    assert request._smello_exc_type == "ValueError"
    assert request._smello_exc_value == "boom"


def test_process_exception_skips_when_config_is_none(factory):
    exc = ValueError("boom")
    exception_calls: list[tuple] = []

    with (
        patch("smello._config", None),
        patch(
            "smello.integrations.django.capture_exception",
            side_effect=lambda *args: exception_calls.append(args),
        ),
    ):
        middleware = _make_middleware()
        request = factory.get("/error")
        middleware.process_exception(request, exc)

    assert len(exception_calls) == 0
    assert not hasattr(request, "_smello_exc_type")
