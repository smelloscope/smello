"""Route-level tests for the API endpoints.

These tests verify HTTP wiring only — Pydantic validation, status codes,
and that each route reaches the right service. Persistence and filter
behavior live in `test_services_*`.
"""

from smello_server.types import (
    EventDetail,
    ExceptionEventData,
    HttpEventData,
    HttpIncomingEventData,
    LogEventData,
)

# --- Typed capture endpoints ---


def test_capture_http_returns_201(client, http_payload):
    resp = client.post("/api/capture/http", json=http_payload)
    assert resp.status_code == 201
    assert resp.json() == {"status": "ok"}

    events = client.get("/api/events").json()
    assert len(events) == 1
    assert events[0]["event_type"] == "http"


def test_capture_http_requires_request_and_response(client):
    resp = client.post("/api/capture/http", json={"duration_ms": 0})
    assert resp.status_code == 422


def test_capture_log_returns_201(client, log_payload):
    resp = client.post("/api/capture/log", json=log_payload)
    assert resp.status_code == 201

    events = client.get("/api/events").json()
    assert events[0]["event_type"] == "log"


def test_capture_log_requires_data(client):
    resp = client.post("/api/capture/log", json={})
    assert resp.status_code == 422


def test_capture_exception_returns_201(client, exception_payload):
    resp = client.post("/api/capture/exception", json=exception_payload)
    assert resp.status_code == 201

    events = client.get("/api/events").json()
    assert events[0]["event_type"] == "exception"


def test_capture_exception_requires_data(client):
    resp = client.post("/api/capture/exception", json={})
    assert resp.status_code == 422


def test_capture_http_incoming_returns_201(client, http_incoming_payload):
    resp = client.post("/api/capture/http_incoming", json=http_incoming_payload)
    assert resp.status_code == 201
    assert resp.json() == {"status": "ok"}

    events = client.get("/api/events").json()
    assert len(events) == 1
    assert events[0]["event_type"] == "http_incoming"


def test_capture_http_incoming_requires_request_and_response(client):
    resp = client.post("/api/capture/http_incoming", json={"duration_ms": 0})
    assert resp.status_code == 422


def test_event_detail_validates_against_typed_union_http_incoming(
    client, http_incoming_payload
):
    client.post("/api/capture/http_incoming", json=http_incoming_payload)
    event_id = client.get("/api/events").json()[0]["id"]
    raw = client.get(f"/api/events/{event_id}").json()
    parsed = EventDetail.model_validate(raw)
    assert isinstance(parsed.data, HttpIncomingEventData)
    assert parsed.data.method == "POST"
    assert parsed.data.path == "/api/users"
    assert parsed.data.framework == "fastapi"
    assert parsed.data.route == "/api/users"
    assert parsed.data.client_ip == "127.0.0.1"


def test_capture_endpoints_marked_deprecated_in_openapi(client):
    spec = client.get("/openapi.json").json()
    assert spec["paths"]["/api/capture"]["post"].get("deprecated") is True
    # Typed endpoints must NOT be deprecated.
    for path in ("/api/capture/http", "/api/capture/log", "/api/capture/exception"):
        assert not spec["paths"][path]["post"].get("deprecated")


# --- Deprecated HTTP-only endpoint ---


def test_deprecated_capture_accepts_http_payload(client, sample_payload):
    resp = client.post("/api/capture", json=sample_payload)
    assert resp.status_code == 201
    events = client.get("/api/events").json()
    assert events[0]["event_type"] == "http"


def test_deprecated_capture_rejects_payload_without_request(client):
    resp = client.post("/api/capture", json={"duration_ms": 0})
    assert resp.status_code == 422


# --- Read endpoints (smoke tests; bulk coverage in test_services_events.py) ---


def test_event_detail_returns_full_data(client, http_payload):
    client.post("/api/capture/http", json=http_payload)
    detail = client.get(f"/api/events/{http_payload['id']}").json()
    assert detail["event_type"] == "http"
    assert detail["data"]["event_type"] == "http"
    assert detail["data"]["method"] == "GET"
    assert detail["data"]["url"] == "https://api.example.com/v1/test"
    assert detail["data"]["host"] == "api.example.com"
    assert detail["data"]["status_code"] == 200


def test_event_detail_validates_against_typed_union_http(client, http_payload):
    client.post("/api/capture/http", json=http_payload)
    raw = client.get(f"/api/events/{http_payload['id']}").json()
    parsed = EventDetail.model_validate(raw)
    assert isinstance(parsed.data, HttpEventData)
    assert parsed.data.method == "GET"
    assert parsed.data.python_version == "3.12.2"
    assert parsed.data.smello_version == "0.1.0"


def test_event_detail_validates_against_typed_union_log(client, log_payload):
    client.post("/api/capture/log", json=log_payload)
    event_id = client.get("/api/events").json()[0]["id"]
    raw = client.get(f"/api/events/{event_id}").json()
    parsed = EventDetail.model_validate(raw)
    assert isinstance(parsed.data, LogEventData)
    assert parsed.data.level == "WARNING"
    assert parsed.data.logger_name == "myapp.auth"


def test_event_detail_validates_against_typed_union_exception(
    client, exception_payload
):
    client.post("/api/capture/exception", json=exception_payload)
    event_id = client.get("/api/events").json()[0]["id"]
    raw = client.get(f"/api/events/{event_id}").json()
    parsed = EventDetail.model_validate(raw)
    assert isinstance(parsed.data, ExceptionEventData)
    assert parsed.data.exc_type == "ValueError"
    assert parsed.data.frames[0].filename == "app.py"


def test_openapi_schema_exposes_discriminated_union(client):
    spec = client.get("/openapi.json").json()
    schemas = spec["components"]["schemas"]
    # Each output model is present.
    assert "HttpEventData" in schemas
    assert "LogEventData" in schemas
    assert "ExceptionEventData" in schemas
    # EventDetail.data is a discriminated union by event_type.
    event_detail = schemas["EventDetail"]
    data_prop = event_detail["properties"]["data"]
    assert "discriminator" in data_prop
    assert data_prop["discriminator"]["propertyName"] == "event_type"


def test_event_not_found(client):
    resp = client.get("/api/events/550e8400-e29b-41d4-a716-446655440000")
    assert resp.status_code == 404


def test_meta_endpoint(client, http_payload):
    client.post("/api/capture/http", json=http_payload)
    data = client.get("/api/meta").json()
    assert data["hosts"] == ["api.example.com"]
    assert data["methods"] == ["GET"]
    assert data["event_types"] == ["http"]


def test_clear_events(client, http_payload):
    client.post("/api/capture/http", json=http_payload)
    assert len(client.get("/api/events").json()) == 1
    resp = client.delete("/api/events")
    assert resp.status_code == 204
    assert client.get("/api/events").json() == []


# --- App and session filtering ---


def test_capture_http_with_app_and_session(client, http_payload):
    http_payload["app"] = "myapp"
    http_payload["session"] = "sess-1"
    client.post("/api/capture/http", json=http_payload)

    detail = client.get(f"/api/events/{http_payload['id']}").json()
    assert detail["app"] == "myapp"
    assert detail["session"] == "sess-1"
    assert detail["data"]["app"] == "myapp"
    assert detail["data"]["session"] == "sess-1"


def test_capture_log_with_app_and_session(client, log_payload):
    log_payload["app"] = "backend"
    log_payload["session"] = "sess-2"
    client.post("/api/capture/log", json=log_payload)

    events = client.get("/api/events").json()
    event_id = events[0]["id"]
    detail = client.get(f"/api/events/{event_id}").json()
    assert detail["app"] == "backend"
    assert detail["session"] == "sess-2"


def test_filter_events_by_app(client, http_payload):
    http_payload["app"] = "frontend"
    client.post("/api/capture/http", json=http_payload)

    payload2 = {**http_payload, "id": None, "app": "backend"}
    client.post("/api/capture/http", json=payload2)

    events = client.get("/api/events?app=frontend").json()
    assert len(events) == 1
    assert events[0]["app"] == "frontend"


def test_filter_events_by_empty_app(client, http_payload):
    client.post("/api/capture/http", json=http_payload)

    payload2 = {**http_payload, "id": None, "app": "myapp"}
    client.post("/api/capture/http", json=payload2)

    events = client.get("/api/events?app=").json()
    assert len(events) == 1
    assert events[0]["app"] == ""


def test_filter_events_by_session(client, http_payload):
    http_payload["session"] = "debug-payment"
    client.post("/api/capture/http", json=http_payload)

    payload2 = {**http_payload, "id": None, "session": "debug-auth"}
    client.post("/api/capture/http", json=payload2)

    events = client.get("/api/events?session=debug-payment").json()
    assert len(events) == 1
    assert events[0]["session"] == "debug-payment"


def test_no_app_param_returns_all(client, http_payload):
    http_payload["app"] = "myapp"
    client.post("/api/capture/http", json=http_payload)

    payload2 = {**http_payload, "id": None, "app": ""}
    client.post("/api/capture/http", json=payload2)

    events = client.get("/api/events").json()
    assert len(events) == 2


def test_meta_includes_apps_and_sessions(client, http_payload):
    http_payload["app"] = "myapp"
    http_payload["session"] = "sess-1"
    client.post("/api/capture/http", json=http_payload)

    meta = client.get("/api/meta").json()
    assert "myapp" in meta["apps"]
    assert "sess-1" in meta["sessions"]


def test_event_summary_includes_app_and_session(client, http_payload):
    http_payload["app"] = "myapp"
    http_payload["session"] = "sess-1"
    client.post("/api/capture/http", json=http_payload)

    events = client.get("/api/events").json()
    assert events[0]["app"] == "myapp"
    assert events[0]["session"] == "sess-1"
