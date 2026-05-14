"""Tests for smello.patches.patch_httpx — sync and async, streaming and non-streaming."""

import asyncio
from unittest.mock import patch

import httpx
import pytest
from smello.config import SmelloConfig
from smello.patches.patch_httpx import patch_httpx


@pytest.fixture()
def config():
    return SmelloConfig(
        server_url="http://test:5110",
        redact_headers=["authorization"],
    )


@pytest.fixture()
def captured(config):
    """Apply patches and return a list that collects send_http payloads."""
    orig_sync_init = httpx.Client.__init__
    orig_async_init = httpx.AsyncClient.__init__
    payloads: list[dict] = []
    with patch("smello.patches.patch_httpx.send_http", side_effect=payloads.append):
        patch_httpx(config)
        yield payloads
    httpx.Client.__init__ = orig_sync_init
    httpx.AsyncClient.__init__ = orig_async_init


def _stream_handler(request: httpx.Request) -> httpx.Response:
    """Mock handler that returns a stream-based response (no pre-set _content)."""
    return httpx.Response(
        200,
        headers={"content-type": "application/json"},
        stream=httpx.ByteStream(b'{"ok":true}'),
    )


# ---- sync non-streaming ----------------------------------------------------


def test_sync_non_streaming_captured(captured):
    transport = httpx.MockTransport(_stream_handler)
    with httpx.Client(transport=transport) as client:
        resp = client.get("https://example.com/api")

    assert resp.status_code == 200
    assert len(captured) == 1
    p = captured[0]
    assert p["request"]["method"] == "GET"
    assert "example.com" in p["request"]["url"]
    assert p["response"]["status_code"] == 200
    assert p["response"]["body"] is not None


def test_sync_non_streaming_body_content(captured):
    transport = httpx.MockTransport(_stream_handler)
    with httpx.Client(transport=transport) as client:
        client.get("https://example.com/data")

    assert "ok" in captured[0]["response"]["body"]


# ---- sync streaming ---------------------------------------------------------


def test_sync_streaming_captured_via_read(captured):
    transport = httpx.MockTransport(_stream_handler)
    with httpx.Client(transport=transport) as client:
        with client.stream("GET", "https://example.com/stream") as resp:
            resp.read()

    assert resp.status_code == 200
    assert len(captured) == 1
    assert "ok" in captured[0]["response"]["body"]


def test_sync_streaming_captured_via_iter_bytes(captured):
    transport = httpx.MockTransport(_stream_handler)
    with httpx.Client(transport=transport) as client:
        with client.stream("GET", "https://example.com/stream") as resp:
            list(resp.iter_bytes())

    assert len(captured) == 1
    assert captured[0]["response"]["body"] is not None


def test_sync_streaming_close_without_read(captured):
    """Closing a streaming response without reading should still capture."""
    transport = httpx.MockTransport(_stream_handler)
    with httpx.Client(transport=transport) as client:
        with client.stream("GET", "https://example.com/stream"):
            pass

    assert len(captured) == 1
    assert captured[0]["response"]["status_code"] == 200


# ---- async non-streaming ---------------------------------------------------


def test_async_non_streaming_captured(captured):
    transport = httpx.MockTransport(_stream_handler)

    async def run():
        async with httpx.AsyncClient(transport=transport) as client:
            return await client.get("https://example.com/api")

    resp = asyncio.run(run())
    assert resp.status_code == 200
    assert len(captured) == 1
    assert captured[0]["response"]["body"] is not None


# ---- async streaming --------------------------------------------------------


def test_async_streaming_captured_via_aread(captured):
    transport = httpx.MockTransport(_stream_handler)

    async def run():
        async with httpx.AsyncClient(transport=transport) as client:
            async with client.stream("GET", "https://example.com/stream") as resp:
                await resp.aread()
        return resp

    resp = asyncio.run(run())
    assert resp.status_code == 200
    assert len(captured) == 1
    assert "ok" in captured[0]["response"]["body"]


def test_async_streaming_captured_via_aiter_bytes(captured):
    transport = httpx.MockTransport(_stream_handler)

    async def run():
        async with httpx.AsyncClient(transport=transport) as client:
            async with client.stream("GET", "https://example.com/stream") as resp:
                _ = [c async for c in resp.aiter_bytes()]

    asyncio.run(run())
    assert len(captured) == 1
    assert captured[0]["response"]["body"] is not None


def test_async_streaming_captured_via_aiter_lines(captured):
    """SSE-style line iteration should still capture the full body."""
    transport = httpx.MockTransport(_stream_handler)

    async def run():
        async with httpx.AsyncClient(transport=transport) as client:
            async with client.stream("GET", "https://example.com/stream") as resp:
                _ = [line async for line in resp.aiter_lines()]

    asyncio.run(run())
    assert len(captured) == 1
    assert captured[0]["response"]["body"] is not None


def test_async_streaming_close_without_read(captured):
    transport = httpx.MockTransport(_stream_handler)

    async def run():
        async with httpx.AsyncClient(transport=transport) as client:
            async with client.stream("GET", "https://example.com/stream"):
                pass

    asyncio.run(run())
    assert len(captured) == 1
    assert captured[0]["response"]["status_code"] == 200


# ---- host filtering --------------------------------------------------------


def test_ignored_host_not_captured(captured, config):
    config.ignore_hosts = ["ignored.example.com"]
    transport = httpx.MockTransport(_stream_handler)
    with httpx.Client(transport=transport) as client:
        client.get("https://ignored.example.com/api")

    assert len(captured) == 0


def test_ignored_host_streaming_not_captured(captured, config):
    config.ignore_hosts = ["ignored.example.com"]
    transport = httpx.MockTransport(_stream_handler)
    with httpx.Client(transport=transport) as client:
        with client.stream("GET", "https://ignored.example.com/s") as resp:
            resp.read()

    assert len(captured) == 0


# ---- header redaction -------------------------------------------------------


def test_authorization_header_redacted(captured):
    transport = httpx.MockTransport(_stream_handler)
    with httpx.Client(transport=transport) as client:
        client.get(
            "https://example.com/api", headers={"Authorization": "Bearer secret"}
        )

    assert captured[0]["request"]["headers"]["authorization"] == "[REDACTED]"


# ---- metadata ---------------------------------------------------------------


def test_library_field_is_httpx(captured):
    transport = httpx.MockTransport(_stream_handler)
    with httpx.Client(transport=transport) as client:
        client.get("https://example.com/api")

    assert captured[0]["meta"]["library"] == "httpx"


def test_duration_is_positive(captured):
    transport = httpx.MockTransport(_stream_handler)
    with httpx.Client(transport=transport) as client:
        client.get("https://example.com/api")

    assert captured[0]["duration_ms"] >= 0


# ---- request body -----------------------------------------------------------


def test_request_body_captured(captured):
    transport = httpx.MockTransport(_stream_handler)
    with httpx.Client(transport=transport) as client:
        client.post("https://example.com/api", json={"key": "value"})

    assert "key" in captured[0]["request"]["body"]


def test_streaming_post_body_captured(captured):
    transport = httpx.MockTransport(_stream_handler)

    async def run():
        async with httpx.AsyncClient(transport=transport) as client:
            async with client.stream(
                "POST", "https://example.com/api", json={"key": "value"}
            ) as resp:
                await resp.aread()

    asyncio.run(run())
    assert len(captured) == 1
    assert "key" in captured[0]["request"]["body"]


# ---- user event hooks preserved ---------------------------------------------


def test_user_event_hooks_preserved(captured):
    """User-provided event hooks should still fire alongside ours."""
    seen = []

    def user_hook(response):
        seen.append(response.status_code)

    transport = httpx.MockTransport(_stream_handler)
    with httpx.Client(
        transport=transport, event_hooks={"response": [user_hook]}
    ) as client:
        client.get("https://example.com/api")

    assert seen == [200]
    assert len(captured) == 1
