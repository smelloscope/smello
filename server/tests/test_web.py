"""Tests for the server web UI routes."""


def test_empty_state(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "No captured requests yet" in resp.text
    assert 'smello.init(server_url="http://localhost:5110")' in resp.text


def test_shows_captured_request(client, make_payload):
    payload = make_payload(
        method="POST", url="https://api.stripe.com/v1/charges", status_code=201
    )
    client.post("/api/capture", json=payload)

    resp = client.get("/")
    assert resp.status_code == 200
    assert "api.stripe.com" in resp.text
    assert "POST" in resp.text
    assert "201" in resp.text


def test_status_badge_classes(client, make_payload):
    client.post("/api/capture", json=make_payload(status_code=404))
    resp = client.get("/")
    assert "status-4xx" in resp.text


def test_status_badge_5xx(client, make_payload):
    client.post("/api/capture", json=make_payload(status_code=500))
    resp = client.get("/")
    assert "status-5xx" in resp.text


def test_status_badge_2xx(client, make_payload):
    client.post("/api/capture", json=make_payload(status_code=200))
    resp = client.get("/")
    assert "status-2xx" in resp.text


def test_shows_multiple_requests(client, make_payload):
    client.post("/api/capture", json=make_payload(url="https://a.com/1"))
    client.post("/api/capture", json=make_payload(url="https://b.com/2"))
    resp = client.get("/")
    assert "a.com" in resp.text
    assert "b.com" in resp.text


def test_detail_page_renders(client, sample_payload):
    sample_payload["request"]["url"] = "https://api.anthropic.com/v1/messages"
    sample_payload["request"]["method"] = "POST"
    sample_payload["request"]["headers"] = {
        "Content-Type": "application/json",
        "X-Api-Key": "[REDACTED]",
    }
    sample_payload["request"]["body"] = '{"model": "claude-sonnet-4-5-20250929"}'
    sample_payload["request"]["body_size"] = 25
    sample_payload["response"]["body"] = '{"id": "msg_abc"}'
    sample_payload["response"]["body_size"] = 17
    sample_payload["duration_ms"] = 1234
    sample_payload["meta"]["library"] = "httpx"
    client.post("/api/capture", json=sample_payload)

    resp = client.get(f"/requests/{sample_payload['id']}")
    assert resp.status_code == 200
    html = resp.text
    assert "POST" in html
    assert "api.anthropic.com/v1/messages" in html
    assert "1234ms" in html
    assert "httpx" in html
    assert "[REDACTED]" in html
    assert "claude-sonnet-4-5-20250929" in html
    assert "msg_abc" in html


def test_detail_page_missing_returns_error(client):
    resp = client.get("/requests/00000000-0000-0000-0000-000000000000")
    assert resp.status_code in (404, 500)
