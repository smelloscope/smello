"""Service-level tests for read functions: list, get, meta, clear."""

import pytest
from smello_server.models import CapturedEvent
from smello_server.services.capture import create_http_event, create_log_event
from smello_server.services.events import (
    clear_events,
    get_event,
    get_meta,
    hydrate_event_data,
    list_events,
)
from smello_server.types import (
    HttpEventData,
    HttpMeta,
    HttpRequestData,
    HttpResponseData,
    LogData,
)


def _http(
    *,
    method: str = "GET",
    url: str = "https://api.example.com/test",
    status_code: int = 200,
    body: str | None = None,
):
    return create_http_event(
        event_id=None,
        duration_ms=10,
        request=HttpRequestData(method=method, url=url, headers={}),
        response=HttpResponseData(
            status_code=status_code, headers={}, body=body, body_size=len(body or "")
        ),
        meta=HttpMeta(library="requests"),
    )


def _log(*, level: str = "INFO", message: str = "hello"):
    return create_log_event(
        event_id=None,
        data=LogData(level=level, logger_name="app", message=message),
    )


@pytest.mark.asyncio
async def test_list_events_empty(services_db):
    assert await list_events() == []


@pytest.mark.asyncio
async def test_list_events_returns_summaries_newest_first(services_db):
    await _http(url="https://a.test/one")
    await _http(url="https://a.test/two")
    rows = await list_events()
    assert len(rows) == 2
    assert {r["event_type"] for r in rows} == {"http"}


@pytest.mark.asyncio
async def test_list_events_filter_by_event_type(services_db):
    await _http()
    await _log(level="WARNING", message="boom")
    rows = await list_events(event_type="log")
    assert len(rows) == 1
    assert rows[0]["event_type"] == "log"


@pytest.mark.asyncio
async def test_list_events_filter_by_method(services_db):
    await _http(method="GET")
    await _http(method="POST")
    rows = await list_events(method="POST")
    assert len(rows) == 1
    assert "POST" in rows[0]["summary"]


@pytest.mark.asyncio
async def test_list_events_filter_by_host(services_db):
    await _http(url="https://api.stripe.com/v1/charges")
    await _http(url="https://api.openai.com/v1/models")
    rows = await list_events(host="api.stripe.com")
    assert len(rows) == 1
    assert "/v1/charges" in rows[0]["summary"]


@pytest.mark.asyncio
async def test_list_events_filter_by_status(services_db):
    await _http(status_code=200)
    await _http(status_code=404)
    rows = await list_events(status=404)
    assert len(rows) == 1
    assert "404" in rows[0]["summary"]


@pytest.mark.asyncio
async def test_list_events_search_summary(services_db):
    await _http()
    await _log(level="WARNING", message="Token expired")
    rows = await list_events(search="Token expired")
    assert len(rows) == 1
    assert rows[0]["event_type"] == "log"


@pytest.mark.asyncio
async def test_list_events_search_data(services_db):
    await _http(body='{"error": "unique-sentinel-value"}')
    await _http()
    rows = await list_events(search="unique-sentinel-value")
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_list_events_limit(services_db):
    for _ in range(5):
        await _http()
    rows = await list_events(limit=2)
    assert len(rows) == 2


@pytest.mark.asyncio
async def test_get_event_returns_none_for_unknown(services_db):
    assert await get_event("550e8400-e29b-41d4-a716-446655440000") is None


@pytest.mark.asyncio
async def test_get_event_returns_event(services_db):
    created = await _http()
    found = await get_event(str(created.id))
    assert found is not None
    assert found.event_type == "http"


@pytest.mark.asyncio
async def test_get_meta_empty(services_db):
    meta = await get_meta()
    assert meta == {"hosts": [], "methods": [], "event_types": []}


@pytest.mark.asyncio
async def test_get_meta_returns_hosts_methods_event_types(services_db):
    await _http(url="https://api.stripe.com/v1/charges")
    await _http(method="POST", url="https://api.openai.com/v1/models")
    await _log(level="WARNING")

    meta = await get_meta()
    assert meta["hosts"] == ["api.openai.com", "api.stripe.com"]
    assert meta["methods"] == ["GET", "POST"]
    assert sorted(meta["event_types"]) == ["http", "log"]


@pytest.mark.asyncio
async def test_clear_events(services_db):
    await _http()
    await _log()
    assert len(await list_events()) == 2
    await clear_events()
    assert await list_events() == []


@pytest.mark.asyncio
async def test_hydrate_event_data_validates_typed_payload(services_db):
    """New writes round-trip through the typed union without modification."""
    created = await _http(method="POST", url="https://x.test/y", status_code=201)
    stored = await CapturedEvent.get(id=created.id)
    typed = hydrate_event_data(stored.event_type, stored.data)
    assert isinstance(typed, HttpEventData)
    assert typed.method == "POST"
    assert typed.status_code == 201


@pytest.mark.asyncio
async def test_hydrate_event_data_backfills_legacy_rows(services_db):
    """Rows written before the typed-output refactor lacked `event_type`
    inside `data`. Hydration should inject it from the column."""
    legacy_data = {
        "duration_ms": 5,
        "method": "GET",
        "url": "https://legacy.test/",
        "host": "legacy.test",
        "request_headers": {},
        "request_body": None,
        "request_body_size": 0,
        "status_code": 200,
        "response_headers": {},
        "response_body": None,
        "response_body_size": 0,
        "library": "requests",
    }
    typed = hydrate_event_data("http", legacy_data)
    assert isinstance(typed, HttpEventData)
    assert typed.event_type == "http"
    assert typed.url == "https://legacy.test/"
