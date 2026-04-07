"""End-to-end test: client SDK captures requests, server stores them via API.

Spins up a real Smello server, patches HTTP libraries via the SDK,
makes requests through them, verifies data appears in the API.
"""

import asyncio
import datetime
import importlib
import json
import socket
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

import aiohttp
import httpx
import pytest
import requests as requests_lib
import tortoise.context
import uvicorn
from smello.config import SmelloConfig
from smello.patches.patch_aiohttp import patch_aiohttp
from smello.patches.patch_httpx import patch_httpx
from smello.patches.patch_requests import patch_requests
from smello.transport import start_worker
from smello_server.app import create_app

# -- Mock target API server ---------------------------------------------------


class _MockTargetHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/redirect-me":
            self.send_response(302)
            self.send_header("Location", "/final-dest")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if "/error" in self.path:
            body = json.dumps({"error": "server error"}).encode()
            status = 500
        else:
            body = json.dumps({"status": "ok", "path": self.path}).encode()
            status = 200
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)
        if self.path == "/post-redirect":
            self.send_response(303)
            self.send_header("Location", "/post-landed")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        body = json.dumps({"received": True}).encode()
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture()
def mock_target():
    """A mock HTTP server acting as the external API being called."""
    server = HTTPServer(("127.0.0.1", 0), _MockTargetHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


@pytest.fixture()
def smello_server(tmp_path):
    """A real Smello server running on a random port with a fresh DB."""
    tortoise.context._global_context = None

    port = _free_port()
    db_url = f"sqlite://{tmp_path / 'e2e_test.db'}"

    app = create_app(db_url=db_url)

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    base = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(f"{base}/api/requests", timeout=1)
            break
        except Exception:
            time.sleep(0.1)

    yield base
    server.should_exit = True
    time.sleep(0.5)
    tortoise.context._global_context = None


@pytest.fixture()
def patched_requests(smello_server):
    """Patch the requests library via smello SDK, return the reloaded module."""
    importlib.reload(requests_lib)

    start_worker(smello_server)
    config = SmelloConfig(server_url=smello_server, redact_headers=["authorization"])
    patch_requests(config)
    return requests_lib


@pytest.fixture()
def patched_httpx(smello_server):
    """Patch httpx (sync + async) via smello SDK, return the reloaded module."""
    importlib.reload(httpx)

    start_worker(smello_server)
    config = SmelloConfig(server_url=smello_server, redact_headers=["authorization"])
    patch_httpx(config)
    return httpx


@pytest.fixture()
def patched_aiohttp(smello_server):
    """Patch aiohttp via smello SDK, return the reloaded module."""
    importlib.reload(aiohttp.client)
    importlib.reload(aiohttp)

    start_worker(smello_server)
    config = SmelloConfig(server_url=smello_server, redact_headers=["authorization"])
    patch_aiohttp(config)
    return aiohttp


# -- Helpers ------------------------------------------------------------------


def _wait_for_capture(smello_url, expected_count=1, timeout=5):
    """Poll the API until the expected number of captured requests appear."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        data = json.loads(urllib.request.urlopen(f"{smello_url}/api/requests").read())
        if len(data) >= expected_count:
            return data
        time.sleep(0.1)
    return json.loads(urllib.request.urlopen(f"{smello_url}/api/requests").read())


def _fetch_json(url):
    return json.loads(urllib.request.urlopen(url).read())


# -- Tests --------------------------------------------------------------------


def test_requests_get_captured(smello_server, mock_target, patched_requests):
    resp = patched_requests.get(f"{mock_target}/e2e-test")
    assert resp.status_code == 200

    data = _wait_for_capture(smello_server)
    assert len(data) >= 1
    assert data[0]["method"] == "GET"
    assert "/e2e-test" in data[0]["url"]
    assert data[0]["status_code"] == 200


def test_httpx_sync_captured(smello_server, mock_target, patched_httpx):
    with patched_httpx.Client() as client:
        resp = client.post(f"{mock_target}/httpx-sync", json={"test": "data"})
    assert resp.status_code == 201

    data = _wait_for_capture(smello_server)
    assert len(data) >= 1
    assert data[0]["method"] == "POST"
    assert "/httpx-sync" in data[0]["url"]
    assert data[0]["status_code"] == 201


def test_httpx_async_captured(smello_server, mock_target, patched_httpx):
    async def make_request():
        async with patched_httpx.AsyncClient() as client:
            return await client.get(f"{mock_target}/httpx-async")

    resp = asyncio.run(make_request())
    assert resp.status_code == 200

    data = _wait_for_capture(smello_server)
    assert len(data) >= 1
    assert data[0]["method"] == "GET"
    assert "/httpx-async" in data[0]["url"]


def test_redacted_headers_in_api(smello_server, mock_target, patched_requests):
    patched_requests.get(
        f"{mock_target}/secret-endpoint",
        headers={"Authorization": "Bearer sk-super-secret-key"},
    )

    data = _wait_for_capture(smello_server)
    detail = _fetch_json(f"{smello_server}/api/requests/{data[0]['id']}")

    # Header key casing depends on the HTTP library; check case-insensitively
    headers_lower = {k.lower(): v for k, v in detail["request_headers"].items()}
    assert headers_lower["authorization"] == "[REDACTED]"
    assert "sk-super-secret-key" not in json.dumps(detail)


def test_aiohttp_get_captured(smello_server, mock_target, patched_aiohttp):
    async def make_request():
        async with patched_aiohttp.ClientSession() as session:
            async with session.get(f"{mock_target}/aiohttp-get") as resp:
                await resp.read()
                return resp

    resp = asyncio.run(make_request())
    assert resp.status == 200

    data = _wait_for_capture(smello_server)
    assert len(data) >= 1
    assert data[0]["method"] == "GET"
    assert "/aiohttp-get" in data[0]["url"]
    assert data[0]["status_code"] == 200


def test_aiohttp_post_captured(smello_server, mock_target, patched_aiohttp):
    async def make_request():
        async with patched_aiohttp.ClientSession() as session:
            async with session.post(
                f"{mock_target}/aiohttp-post", json={"test": "data"}
            ) as resp:
                await resp.read()
                return resp

    resp = asyncio.run(make_request())
    assert resp.status == 201

    data = _wait_for_capture(smello_server)
    assert len(data) >= 1
    assert data[0]["method"] == "POST"
    assert "/aiohttp-post" in data[0]["url"]
    assert data[0]["status_code"] == 201

    detail = _fetch_json(f"{smello_server}/api/requests/{data[0]['id']}")
    assert detail["request_body"] == json.dumps({"test": "data"})


def test_aiohttp_post_str_data(smello_server, mock_target, patched_aiohttp):
    async def make_request():
        async with patched_aiohttp.ClientSession() as session:
            async with session.post(
                f"{mock_target}/aiohttp-str", data="hello world"
            ) as resp:
                await resp.read()
                return resp

    resp = asyncio.run(make_request())
    assert resp.status == 201

    data = _wait_for_capture(smello_server)
    assert len(data) >= 1

    detail = _fetch_json(f"{smello_server}/api/requests/{data[0]['id']}")
    assert detail["request_body"] == "hello world"


def test_aiohttp_post_bytes_data(smello_server, mock_target, patched_aiohttp):
    async def make_request():
        async with patched_aiohttp.ClientSession() as session:
            async with session.post(
                f"{mock_target}/aiohttp-bytes", data=b'{"raw": true}'
            ) as resp:
                await resp.read()
                return resp

    resp = asyncio.run(make_request())
    assert resp.status == 201

    data = _wait_for_capture(smello_server)
    assert len(data) >= 1

    detail = _fetch_json(f"{smello_server}/api/requests/{data[0]['id']}")
    assert detail["request_body"] == '{"raw": true}'


def test_aiohttp_ignored_host_not_captured(smello_server, mock_target):
    """Requests to ignored hosts pass through without being captured."""
    importlib.reload(aiohttp.client)
    importlib.reload(aiohttp)

    ignored_host = urlparse(mock_target).hostname
    start_worker(smello_server)
    config = SmelloConfig(
        server_url=smello_server,
        redact_headers=["authorization"],
        ignore_hosts=[ignored_host],
    )
    patch_aiohttp(config)

    async def make_request():
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{mock_target}/should-be-ignored") as resp:
                await resp.read()
                return resp

    resp = asyncio.run(make_request())
    assert resp.status == 200

    # Give the worker a moment, then verify the ignored request was not captured
    time.sleep(1)
    data = json.loads(urllib.request.urlopen(f"{smello_server}/api/requests").read())
    captured_urls = [r["url"] for r in data]
    assert not any("/should-be-ignored" in url for url in captured_urls)


def test_aiohttp_response_readable_after_capture(
    smello_server, mock_target, patched_aiohttp
):
    """Caller can still read the response body after the patch captures it."""

    async def make_request():
        async with patched_aiohttp.ClientSession() as session:
            async with session.get(f"{mock_target}/aiohttp-readable") as resp:
                body = await resp.read()
                return body

    body = asyncio.run(make_request())
    parsed = json.loads(body)
    assert parsed["status"] == "ok"
    assert "/aiohttp-readable" in parsed["path"]


def test_aiohttp_streaming_not_consumed(smello_server, mock_target, patched_aiohttp):
    # Protects against the patch eagerly calling response.read(), which
    # would exhaust the internal StreamReader before the caller can
    # iterate over it via response.content (iter_chunked, iter_any, SSE).
    async def make_request():
        async with patched_aiohttp.ClientSession() as session:
            async with session.get(f"{mock_target}/aiohttp-stream") as resp:
                chunks = []
                async for chunk in resp.content.iter_chunked(1024):
                    chunks.append(chunk)
                return resp.status, b"".join(chunks)

    status, body = asyncio.run(make_request())
    assert status == 200
    parsed = json.loads(body)
    assert parsed["status"] == "ok"

    # The request should still be captured (via the release hook) even
    # though the caller never called resp.read().
    data = _wait_for_capture(smello_server)
    captured_urls = [r["url"] for r in data]
    assert any("/aiohttp-stream" in url for url in captured_urls)


def test_aiohttp_custom_json_serializer(smello_server, mock_target, patched_aiohttp):
    # Protects against the patch calling json.dumps() on objects that
    # only the session's custom json_serialize can handle. If stdlib
    # serialization fails, the request must still proceed — the capture
    # can drop the request body gracefully instead of raising before
    # the request is ever sent.
    def custom_serializer(obj):
        return json.dumps(obj, default=str)

    async def make_request():
        async with patched_aiohttp.ClientSession(
            json_serialize=custom_serializer
        ) as session:
            async with session.post(
                f"{mock_target}/aiohttp-custom-json",
                json={"ts": datetime.datetime(2024, 1, 1)},
            ) as resp:
                await resp.read()
                return resp

    resp = asyncio.run(make_request())
    assert resp.status == 201

    data = _wait_for_capture(smello_server)
    assert any("/aiohttp-custom-json" in r["url"] for r in data)


def test_aiohttp_base_url_ignore_hosts(smello_server, mock_target):
    # Protects against ignore_hosts silently failing for base_url sessions.
    # When ClientSession(base_url=...) is used, str_or_url is a relative
    # path like "/path" whose hostname is empty. The patch must resolve
    # the actual host from response.url — not the relative path — so that
    # ignore_hosts filtering works correctly.
    importlib.reload(aiohttp.client)
    importlib.reload(aiohttp)

    ignored_host = urlparse(mock_target).hostname
    start_worker(smello_server)
    config = SmelloConfig(
        server_url=smello_server,
        redact_headers=["authorization"],
        ignore_hosts=[ignored_host],
    )
    patch_aiohttp(config)

    async def make_request():
        async with aiohttp.ClientSession(base_url=mock_target) as session:
            async with session.get("/base-url-ignored") as resp:
                await resp.read()
                return resp

    resp = asyncio.run(make_request())
    assert resp.status == 200

    time.sleep(1)
    data = json.loads(urllib.request.urlopen(f"{smello_server}/api/requests").read())
    captured_urls = [r["url"] for r in data]
    assert not any("/base-url-ignored" in url for url in captured_urls)


def test_aiohttp_session_headers_captured(smello_server, mock_target, patched_aiohttp):
    # Protects against capturing only the kwargs["headers"] subset and
    # missing session-level defaults (auth, cookies, Content-Type added
    # by ClientSession). The patch must use response.request_info.headers
    # which contains the actual headers sent on the wire.
    async def make_request():
        async with patched_aiohttp.ClientSession(
            headers={"X-Session-Default": "from-session"}
        ) as session:
            async with session.get(
                f"{mock_target}/aiohttp-sess-hdr",
                headers={"X-Per-Request": "per-req"},
            ) as resp:
                await resp.read()
                return resp

    resp = asyncio.run(make_request())
    assert resp.status == 200

    data = _wait_for_capture(smello_server)
    matching = [r for r in data if "/aiohttp-sess-hdr" in r["url"]]
    assert len(matching) >= 1

    detail = _fetch_json(f"{smello_server}/api/requests/{matching[0]['id']}")
    headers_lower = {k.lower(): v for k, v in detail["request_headers"].items()}
    assert headers_lower["x-session-default"] == "from-session"
    assert headers_lower["x-per-request"] == "per-req"


def test_aiohttp_raise_for_status_captured(smello_server, mock_target, patched_aiohttp):
    # Protects against losing captures when raise_for_status=True.
    # aiohttp raises ClientResponseError inside _request() before
    # returning the response object, so the normal read/release hooks
    # never fire. The patch must catch the exception, capture the
    # request from the error metadata, and re-raise.
    async def make_request():
        async with patched_aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.get(f"{mock_target}/error-500") as resp:
                await resp.read()

    with pytest.raises(patched_aiohttp.ClientResponseError) as exc_info:
        asyncio.run(make_request())
    assert exc_info.value.status == 500

    data = _wait_for_capture(smello_server)
    matching = [r for r in data if "/error-500" in r["url"]]
    assert len(matching) >= 1
    assert matching[0]["status_code"] == 500


def test_aiohttp_post_dict_data(smello_server, mock_target, patched_aiohttp):
    # Protects against losing request bodies for the common aiohttp
    # form-post pattern: data={"key": "val"}. aiohttp serializes dicts
    # as application/x-www-form-urlencoded internally; the patch must
    # do the same instead of recording request_body as None.
    async def make_request():
        async with patched_aiohttp.ClientSession() as session:
            async with session.post(
                f"{mock_target}/aiohttp-form",
                data={"username": "alice", "role": "admin"},
            ) as resp:
                await resp.read()
                return resp

    resp = asyncio.run(make_request())
    assert resp.status == 201

    data = _wait_for_capture(smello_server)
    matching = [r for r in data if "/aiohttp-form" in r["url"]]
    assert len(matching) >= 1

    detail = _fetch_json(f"{smello_server}/api/requests/{matching[0]['id']}")
    assert "username=alice" in detail["request_body"]
    assert "role=admin" in detail["request_body"]


def test_aiohttp_redirect_hops_captured(smello_server, mock_target, patched_aiohttp):
    # Protects against losing intermediate 3xx redirect responses.
    # aiohttp follows the entire redirect chain inside _request()
    # before returning, so only the final response is visible to the
    # wrapper. The patch must iterate response.history to capture each
    # intermediate hop, otherwise redirect-heavy flows appear incomplete
    # in the dashboard.
    async def make_request():
        async with patched_aiohttp.ClientSession() as session:
            async with session.get(f"{mock_target}/redirect-me") as resp:
                await resp.read()
                return resp

    resp = asyncio.run(make_request())
    assert resp.status == 200
    assert "/final-dest" in str(resp.url)

    # Wait for at least 2 captures: the 302 hop + the final 200
    data = _wait_for_capture(smello_server, expected_count=2)

    redirect_hop = [r for r in data if "/redirect-me" in r["url"]]
    assert len(redirect_hop) >= 1
    assert redirect_hop[0]["status_code"] == 302

    final_resp = [r for r in data if "/final-dest" in r["url"]]
    assert len(final_resp) >= 1
    assert final_resp[0]["status_code"] == 200


def test_aiohttp_redirect_method_change(smello_server, mock_target, patched_aiohttp):
    # Protects against recording the final response with the original
    # HTTP method after a method-changing redirect.  A POST that receives
    # a 303 is retried as GET by aiohttp.  The patch must use
    # response.request_info.method for the final capture, and must not
    # attach the original POST body to the redirected GET.
    async def make_request():
        async with patched_aiohttp.ClientSession() as session:
            async with session.post(
                f"{mock_target}/post-redirect", json={"payload": 1}
            ) as resp:
                await resp.read()
                return resp

    resp = asyncio.run(make_request())
    assert resp.status == 200

    # Wait for 2 captures: the 303 hop + the final 200
    data = _wait_for_capture(smello_server, expected_count=2)

    # The intermediate 303 should be recorded as POST
    hop = [r for r in data if "/post-redirect" in r["url"]]
    assert len(hop) >= 1
    assert hop[0]["status_code"] == 303

    # The final response should be recorded as GET (not POST)
    # and must not carry the original POST body.
    final = [r for r in data if "/post-landed" in r["url"]]
    assert len(final) >= 1
    assert final[0]["method"] == "GET"
    assert final[0]["status_code"] == 200

    detail = _fetch_json(f"{smello_server}/api/requests/{final[0]['id']}")
    assert detail["request_body"] is None


def test_aiohttp_close_without_read(smello_server, mock_target, patched_aiohttp):
    # Protects against silently dropping captures when the caller uses
    # resp.close() instead of the async-with context manager.  The patch
    # hooks release() for context-managed responses but close() is a
    # separate code path.  Both must trigger the capture.
    async def make_request():
        session = patched_aiohttp.ClientSession()
        resp = await session._request("GET", f"{mock_target}/aiohttp-close")
        resp.close()
        await session.close()

    asyncio.run(make_request())

    data = _wait_for_capture(smello_server)
    matching = [r for r in data if "/aiohttp-close" in r["url"]]
    assert len(matching) >= 1
    assert matching[0]["status_code"] == 200
