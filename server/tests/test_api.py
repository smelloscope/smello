"""Tests for the server API endpoints."""


# --- HTTP event capture (legacy format, backwards-compatible) ---


def test_capture_returns_201(client, sample_payload):
    resp = client.post("/api/capture", json=sample_payload)
    assert resp.status_code == 201
    assert resp.json() == {"status": "ok"}


def test_capture_stores_http_event(client, sample_payload):
    client.post("/api/capture", json=sample_payload)
    data = client.get("/api/events").json()
    assert len(data) == 1
    assert data[0]["event_type"] == "http"
    assert "GET /v1/test" in data[0]["summary"]
    assert "200" in data[0]["summary"]


def test_capture_auto_generates_id(client, sample_payload):
    sample_payload.pop("id")
    resp = client.post("/api/capture", json=sample_payload)
    assert resp.status_code == 201
    data = client.get("/api/events").json()
    assert len(data) == 1
    assert data[0]["id"]


def test_http_event_detail(client, sample_payload):
    client.post("/api/capture", json=sample_payload)
    resp = client.get(f"/api/events/{sample_payload['id']}")
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["event_type"] == "http"
    assert detail["data"]["method"] == "GET"
    assert detail["data"]["url"] == "https://api.example.com/v1/test"
    assert detail["data"]["host"] == "api.example.com"
    assert detail["data"]["status_code"] == 200
    assert detail["data"]["duration_ms"] == 150
    assert detail["data"]["request_headers"] == {"Content-Type": "application/json"}
    assert detail["data"]["response_body"] == '{"result": "success"}'
    assert detail["data"]["library"] == "requests"


def test_capture_uppercases_method(client, make_payload):
    client.post("/api/capture", json=make_payload(method="post"))
    data = client.get("/api/events").json()
    detail = client.get(f"/api/events/{data[0]['id']}").json()
    assert detail["data"]["method"] == "POST"


def test_capture_extracts_host(client, make_payload):
    client.post(
        "/api/capture", json=make_payload(url="https://api.stripe.com/v1/charges")
    )
    data = client.get("/api/events").json()
    detail = client.get(f"/api/events/{data[0]['id']}").json()
    assert detail["data"]["host"] == "api.stripe.com"


# --- Filtering ---


def test_empty_list(client):
    resp = client.get("/api/events")
    assert resp.status_code == 200
    assert resp.json() == []


def test_filter_by_event_type(client, make_payload, sample_log_payload):
    client.post("/api/capture", json=make_payload())
    client.post("/api/capture", json=sample_log_payload)
    data = client.get("/api/events", params={"event_type": "log"}).json()
    assert len(data) == 1
    assert data[0]["event_type"] == "log"


def test_filter_by_method(client, make_payload):
    client.post("/api/capture", json=make_payload(method="GET"))
    client.post("/api/capture", json=make_payload(method="POST"))
    data = client.get("/api/events", params={"method": "POST"}).json()
    assert len(data) == 1
    assert "POST" in data[0]["summary"]


def test_filter_by_host(client, make_payload):
    client.post(
        "/api/capture", json=make_payload(url="https://api.stripe.com/v1/charges")
    )
    client.post(
        "/api/capture", json=make_payload(url="https://api.openai.com/v1/models")
    )
    data = client.get("/api/events", params={"host": "api.stripe.com"}).json()
    assert len(data) == 1
    assert "stripe" in data[0]["summary"] or "stripe" in str(
        client.get(f"/api/events/{data[0]['id']}").json()["data"]
    )


def test_filter_by_status(client, make_payload):
    client.post("/api/capture", json=make_payload(status_code=200))
    client.post("/api/capture", json=make_payload(status_code=404))
    data = client.get("/api/events", params={"status": 404}).json()
    assert len(data) == 1
    assert "404" in data[0]["summary"]


def test_search_by_summary(client, make_payload, sample_log_payload):
    client.post("/api/capture", json=make_payload())
    client.post("/api/capture", json=sample_log_payload)
    data = client.get("/api/events", params={"search": "Token expired"}).json()
    assert len(data) == 1
    assert data[0]["event_type"] == "log"


def test_search_by_data(client, make_payload):
    payload = make_payload()
    payload["response"]["body"] = '{"error": "unique-sentinel-value"}'
    client.post("/api/capture", json=payload)
    client.post("/api/capture", json=make_payload())
    data = client.get("/api/events", params={"search": "unique-sentinel-value"}).json()
    assert len(data) == 1


def test_limit(client, make_payload):
    for _ in range(5):
        client.post("/api/capture", json=make_payload())
    data = client.get("/api/events", params={"limit": 2}).json()
    assert len(data) == 2


# --- Log events ---


def test_capture_log_event(client, sample_log_payload):
    resp = client.post("/api/capture", json=sample_log_payload)
    assert resp.status_code == 201

    data = client.get("/api/events").json()
    assert len(data) == 1
    assert data[0]["event_type"] == "log"
    assert "WARNING" in data[0]["summary"]
    assert "myapp.auth" in data[0]["summary"]
    assert "Token expired" in data[0]["summary"]


def test_log_event_detail(client, sample_log_payload):
    client.post("/api/capture", json=sample_log_payload)
    events = client.get("/api/events").json()
    detail = client.get(f"/api/events/{events[0]['id']}").json()
    assert detail["data"]["level"] == "WARNING"
    assert detail["data"]["logger_name"] == "myapp.auth"
    assert detail["data"]["message"] == "Token expired for user 42"
    assert detail["data"]["pathname"] == "/app/auth.py"
    assert detail["data"]["lineno"] == 87


def test_log_event_requires_data(client):
    resp = client.post("/api/capture", json={"event_type": "log"})
    assert resp.status_code == 422


# --- Exception events ---


def test_capture_exception_event(client, sample_exception_payload):
    resp = client.post("/api/capture", json=sample_exception_payload)
    assert resp.status_code == 201

    data = client.get("/api/events").json()
    assert len(data) == 1
    assert data[0]["event_type"] == "exception"
    assert "ValueError" in data[0]["summary"]


def test_exception_event_detail(client, sample_exception_payload):
    client.post("/api/capture", json=sample_exception_payload)
    events = client.get("/api/events").json()
    detail = client.get(f"/api/events/{events[0]['id']}").json()
    assert detail["data"]["exc_type"] == "ValueError"
    assert "invalid literal" in detail["data"]["exc_value"]
    assert detail["data"]["frames"][0]["filename"] == "app.py"
    assert detail["data"]["frames"][0]["lineno"] == 42
    assert "Traceback" in detail["data"]["traceback_text"]


def test_exception_event_requires_data(client):
    resp = client.post("/api/capture", json={"event_type": "exception"})
    assert resp.status_code == 422


# --- Unknown event type ---


def test_unknown_event_type_rejected(client):
    resp = client.post(
        "/api/capture",
        json={"event_type": "unknown", "data": {"foo": "bar"}},
    )
    assert resp.status_code == 422


# --- Meta ---


def test_meta_empty(client):
    resp = client.get("/api/meta")
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"hosts": [], "methods": [], "event_types": []}


def test_meta_returns_hosts_methods_and_event_types(
    client, make_payload, sample_log_payload
):
    client.post(
        "/api/capture", json=make_payload(url="https://api.stripe.com/v1/charges")
    )
    client.post(
        "/api/capture",
        json=make_payload(method="POST", url="https://api.openai.com/v1/models"),
    )
    client.post("/api/capture", json=sample_log_payload)

    data = client.get("/api/meta").json()
    assert data["hosts"] == ["api.openai.com", "api.stripe.com"]
    assert data["methods"] == ["GET", "POST"]
    assert sorted(data["event_types"]) == ["http", "log"]


# --- Clear ---


def test_clear_all(client, sample_payload, sample_log_payload):
    client.post("/api/capture", json=sample_payload)
    client.post("/api/capture", json=sample_log_payload)
    assert len(client.get("/api/events").json()) == 2

    resp = client.delete("/api/events")
    assert resp.status_code == 204
    assert len(client.get("/api/events").json()) == 0


def test_event_not_found(client):
    resp = client.get("/api/events/550e8400-e29b-41d4-a716-446655440000")
    assert resp.status_code == 404
