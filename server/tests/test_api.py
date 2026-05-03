"""Route-level tests for the API endpoints.

These tests verify HTTP wiring only — Pydantic validation, status codes,
and that each route reaches the right service. Persistence and filter
behavior live in `test_services_*`.
"""

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
    assert detail["data"]["method"] == "GET"
    assert detail["data"]["url"] == "https://api.example.com/v1/test"
    assert detail["data"]["host"] == "api.example.com"
    assert detail["data"]["status_code"] == 200


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
