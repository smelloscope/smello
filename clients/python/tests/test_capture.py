"""Tests for smello.capture serialization."""

import pytest
from smello.capture import serialize_request_response
from smello.config import SmelloConfig


@pytest.fixture()
def config():
    return SmelloConfig(
        server_url="http://test:5110", redact_headers=["authorization", "x-api-key"]
    )


@pytest.fixture()
def basic_payload(config):
    return serialize_request_response(
        config=config,
        method="GET",
        url="https://api.example.com/test",
        request_headers={"Content-Type": "application/json"},
        request_body=None,
        status_code=200,
        response_headers={"Content-Type": "application/json"},
        response_body='{"ok": true}',
        duration_s=0.15,
        library="requests",
    )


def test_basic_fields(basic_payload):
    assert basic_payload["duration_ms"] == 150
    assert basic_payload["request"]["method"] == "GET"
    assert basic_payload["request"]["url"] == "https://api.example.com/test"
    assert basic_payload["response"]["status_code"] == 200
    assert basic_payload["response"]["body"] == '{"ok": true}'
    assert basic_payload["meta"]["library"] == "requests"
    assert "id" in basic_payload
    assert "timestamp" in basic_payload


def test_null_body(basic_payload):
    assert basic_payload["request"]["body"] is None
    assert basic_payload["request"]["body_size"] == 0


def test_header_redaction(config):
    payload = serialize_request_response(
        config=config,
        method="POST",
        url="https://example.com",
        request_headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer sk-secret",
            "X-Api-Key": "key_12345",
            "X-Custom": "keep-this",
        },
        request_body=None,
        status_code=200,
        response_headers={},
        response_body=None,
        duration_s=0.1,
        library="httpx",
    )
    headers = payload["request"]["headers"]
    assert headers["Content-Type"] == "application/json"
    assert headers["Authorization"] == "[REDACTED]"
    assert headers["X-Api-Key"] == "[REDACTED]"
    assert headers["X-Custom"] == "keep-this"


def test_custom_redact_headers():
    config = SmelloConfig(server_url="http://test:5110", redact_headers=["x-secret"])
    payload = serialize_request_response(
        config=config,
        method="GET",
        url="https://example.com",
        request_headers={"Authorization": "Bearer token", "X-Secret": "hidden"},
        request_body=None,
        status_code=200,
        response_headers={},
        response_body=None,
        duration_s=0.05,
        library="requests",
    )
    headers = payload["request"]["headers"]
    assert headers["Authorization"] == "Bearer token"
    assert headers["X-Secret"] == "[REDACTED]"


def test_bytes_body_utf8(config):
    payload = serialize_request_response(
        config=config,
        method="POST",
        url="https://example.com",
        request_headers={},
        request_body=b'{"key": "value"}',
        status_code=200,
        response_headers={},
        response_body=b'{"result": "ok"}',
        duration_s=0.1,
        library="requests",
    )
    assert payload["request"]["body"] == '{"key": "value"}'
    assert payload["request"]["body_size"] == 16
    assert payload["response"]["body"] == '{"result": "ok"}'


def test_binary_body_non_utf8(config):
    binary_data = bytes(range(256))
    payload = serialize_request_response(
        config=config,
        method="POST",
        url="https://example.com",
        request_headers={},
        request_body=binary_data,
        status_code=200,
        response_headers={},
        response_body=None,
        duration_s=0.1,
        library="requests",
    )
    assert payload["request"]["body"] == "<binary: 256 bytes>"
    assert payload["request"]["body_size"] == 256


def test_string_body(config):
    payload = serialize_request_response(
        config=config,
        method="POST",
        url="https://example.com",
        request_headers={},
        request_body="plain text",
        status_code=200,
        response_headers={},
        response_body="response text",
        duration_s=0.1,
        library="httpx",
    )
    assert payload["request"]["body"] == "plain text"
    assert payload["response"]["body"] == "response text"


def test_duration_rounding(config):
    payload = serialize_request_response(
        config=config,
        method="GET",
        url="https://example.com",
        request_headers={},
        request_body=None,
        status_code=200,
        response_headers={},
        response_body=None,
        duration_s=1.5678,
        library="requests",
    )
    assert payload["duration_ms"] == 1567
