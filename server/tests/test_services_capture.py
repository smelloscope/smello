"""Service-level tests for capture (write) functions."""

import pytest
from smello_server.models import CapturedEvent
from smello_server.services.capture import (
    create_exception_event,
    create_http_event,
    create_log_event,
)
from smello_server.types import (
    ExceptionData,
    ExceptionFrame,
    HttpMeta,
    HttpRequestData,
    HttpResponseData,
    LogData,
)


@pytest.mark.asyncio
async def test_create_http_event_persists_row(services_db):
    event = await create_http_event(
        event_id="550e8400-e29b-41d4-a716-446655440000",
        duration_ms=150,
        request=HttpRequestData(
            method="get",
            url="https://api.example.com/v1/test",
            headers={"Content-Type": "application/json"},
        ),
        response=HttpResponseData(
            status_code=200,
            headers={"Content-Type": "application/json"},
            body='{"result": "success"}',
            body_size=21,
        ),
        meta=HttpMeta(library="requests"),
    )

    stored = await CapturedEvent.get(id=event.id)
    assert stored.event_type == "http"
    assert stored.summary == "GET /v1/test → 200"
    assert stored.data["event_type"] == "http"
    assert stored.data["method"] == "GET"
    assert stored.data["host"] == "api.example.com"
    assert stored.data["status_code"] == 200
    assert stored.data["duration_ms"] == 150
    assert stored.data["library"] == "requests"


@pytest.mark.asyncio
async def test_create_http_event_persists_meta_fields(services_db):
    """python_version and smello_version are now first-class output fields."""
    event = await create_http_event(
        event_id=None,
        duration_ms=0,
        request=HttpRequestData(method="GET", url="https://x.test/", headers={}),
        response=HttpResponseData(status_code=200, headers={}),
        meta=HttpMeta(library="httpx", python_version="3.12.2", smello_version="0.4.0"),
    )
    stored = await CapturedEvent.get(id=event.id)
    assert stored.data["python_version"] == "3.12.2"
    assert stored.data["smello_version"] == "0.4.0"


@pytest.mark.asyncio
async def test_create_http_event_auto_generates_id(services_db):
    event = await create_http_event(
        event_id=None,
        duration_ms=0,
        request=HttpRequestData(method="GET", url="https://x.test/", headers={}),
        response=HttpResponseData(status_code=200, headers={}),
        meta=HttpMeta(),
    )
    assert event.id is not None
    assert str(event.id)


@pytest.mark.asyncio
async def test_create_http_event_uppercases_method(services_db):
    event = await create_http_event(
        event_id=None,
        duration_ms=0,
        request=HttpRequestData(method="post", url="https://x.test/", headers={}),
        response=HttpResponseData(status_code=201, headers={}),
        meta=HttpMeta(),
    )
    stored = await CapturedEvent.get(id=event.id)
    assert stored.data["method"] == "POST"
    assert "POST" in stored.summary


@pytest.mark.asyncio
async def test_create_log_event_persists_row(services_db):
    event = await create_log_event(
        event_id=None,
        data=LogData(
            level="WARNING",
            logger_name="myapp.auth",
            message="Token expired for user 42",
            pathname="/app/auth.py",
            lineno=87,
            func_name="validate_token",
        ),
    )

    stored = await CapturedEvent.get(id=event.id)
    assert stored.event_type == "log"
    assert stored.summary == "WARNING myapp.auth: Token expired for user 42"
    assert stored.data["event_type"] == "log"
    assert stored.data["level"] == "WARNING"
    assert stored.data["pathname"] == "/app/auth.py"
    assert stored.data["lineno"] == 87


@pytest.mark.asyncio
async def test_create_log_event_truncates_long_message(services_db):
    long_msg = "x" * 500
    event = await create_log_event(
        event_id=None,
        data=LogData(level="INFO", logger_name="big", message=long_msg),
    )
    stored = await CapturedEvent.get(id=event.id)
    assert "…" in stored.summary
    assert len(stored.summary) < 250


@pytest.mark.asyncio
async def test_create_exception_event_persists_row(services_db):
    event = await create_exception_event(
        event_id=None,
        data=ExceptionData(
            exc_type="ValueError",
            exc_value="invalid literal for int() with base 10: 'abc'",
            exc_module="builtins",
            traceback_text="Traceback...\nValueError: invalid\n",
            frames=[
                ExceptionFrame(
                    filename="app.py",
                    lineno=42,
                    function="main",
                    context_line="    x = int(user_input)",
                )
            ],
        ),
    )

    stored = await CapturedEvent.get(id=event.id)
    assert stored.event_type == "exception"
    assert stored.summary.startswith("ValueError: invalid literal")
    assert stored.data["event_type"] == "exception"
    assert stored.data["exc_type"] == "ValueError"
    assert stored.data["frames"][0]["filename"] == "app.py"
    assert stored.data["frames"][0]["pre_context"] == []
