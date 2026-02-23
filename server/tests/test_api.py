"""Tests for the server API endpoints."""


def test_capture_returns_201(client, sample_payload):
    resp = client.post("/api/capture", json=sample_payload)
    assert resp.status_code == 201
    assert resp.json() == {"status": "ok"}


def test_capture_stores_request(client, sample_payload):
    client.post("/api/capture", json=sample_payload)
    data = client.get("/api/requests").json()
    assert len(data) == 1
    assert data[0]["method"] == "GET"
    assert data[0]["url"] == "https://api.example.com/v1/test"
    assert data[0]["host"] == "api.example.com"
    assert data[0]["status_code"] == 200
    assert data[0]["duration_ms"] == 150


def test_capture_auto_generates_id(client, sample_payload):
    sample_payload.pop("id")
    resp = client.post("/api/capture", json=sample_payload)
    assert resp.status_code == 201
    data = client.get("/api/requests").json()
    assert len(data) == 1
    assert data[0]["id"]


def test_capture_extracts_host(client, make_payload):
    client.post(
        "/api/capture", json=make_payload(url="https://api.stripe.com/v1/charges")
    )
    data = client.get("/api/requests").json()
    assert data[0]["host"] == "api.stripe.com"


def test_capture_uppercases_method(client, make_payload):
    client.post("/api/capture", json=make_payload(method="post"))
    data = client.get("/api/requests").json()
    assert data[0]["method"] == "POST"


def test_empty_list(client):
    resp = client.get("/api/requests")
    assert resp.status_code == 200
    assert resp.json() == []


def test_filter_by_method(client, make_payload):
    client.post("/api/capture", json=make_payload(method="GET"))
    client.post("/api/capture", json=make_payload(method="POST"))
    data = client.get("/api/requests", params={"method": "POST"}).json()
    assert len(data) == 1
    assert data[0]["method"] == "POST"


def test_filter_by_host(client, make_payload):
    client.post(
        "/api/capture", json=make_payload(url="https://api.stripe.com/v1/charges")
    )
    client.post(
        "/api/capture", json=make_payload(url="https://api.openai.com/v1/models")
    )
    data = client.get("/api/requests", params={"host": "api.stripe.com"}).json()
    assert len(data) == 1
    assert data[0]["host"] == "api.stripe.com"


def test_filter_by_status(client, make_payload):
    client.post("/api/capture", json=make_payload(status_code=200))
    client.post("/api/capture", json=make_payload(status_code=404))
    data = client.get("/api/requests", params={"status": 404}).json()
    assert len(data) == 1
    assert data[0]["status_code"] == 404


def test_search_by_url(client, make_payload):
    client.post(
        "/api/capture", json=make_payload(url="https://api.stripe.com/v1/charges")
    )
    client.post(
        "/api/capture", json=make_payload(url="https://api.openai.com/v1/models")
    )
    data = client.get("/api/requests", params={"search": "stripe"}).json()
    assert len(data) == 1
    assert "stripe" in data[0]["url"]


def test_limit(client, make_payload):
    for _ in range(5):
        client.post("/api/capture", json=make_payload())
    data = client.get("/api/requests", params={"limit": 2}).json()
    assert len(data) == 2


def test_get_request_detail(client, sample_payload):
    client.post("/api/capture", json=sample_payload)
    resp = client.get(f"/api/requests/{sample_payload['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == sample_payload["id"]
    assert data["method"] == "GET"
    assert data["url"] == "https://api.example.com/v1/test"
    assert data["request_headers"] == {"Content-Type": "application/json"}
    assert data["response_body"] == '{"result": "success"}'
    assert data["response_body_size"] == 21
    assert data["library"] == "requests"


def test_get_request_not_found(client):
    resp = client.get("/api/requests/550e8400-e29b-41d4-a716-446655440000")
    assert resp.status_code == 404


def test_meta_empty(client):
    resp = client.get("/api/meta")
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"hosts": [], "methods": []}


def test_meta_returns_distinct_hosts_and_methods(client, make_payload):
    client.post(
        "/api/capture", json=make_payload(url="https://api.stripe.com/v1/charges")
    )
    client.post(
        "/api/capture",
        json=make_payload(method="POST", url="https://api.openai.com/v1/models"),
    )
    client.post(
        "/api/capture",
        json=make_payload(method="POST", url="https://api.stripe.com/v1/refunds"),
    )

    data = client.get("/api/meta").json()
    assert data["hosts"] == ["api.openai.com", "api.stripe.com"]
    assert data["methods"] == ["GET", "POST"]


def test_clear_all(client, sample_payload):
    client.post("/api/capture", json=sample_payload)
    assert len(client.get("/api/requests").json()) == 1

    resp = client.delete("/api/requests")
    assert resp.status_code == 204
    assert len(client.get("/api/requests").json()) == 0
