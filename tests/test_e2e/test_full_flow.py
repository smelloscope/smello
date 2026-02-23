"""End-to-end test: client SDK captures requests, server stores them via API.

Spins up a real Smello server, patches HTTP libraries via the SDK,
makes requests through them, verifies data appears in the API.
"""

import asyncio
import importlib
import json
import socket
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

import httpx
import pytest
import requests as requests_lib
import tortoise.context
import uvicorn
from smello.config import SmelloConfig
from smello.patches.patch_httpx import patch_httpx
from smello.patches.patch_requests import patch_requests
from smello.transport import start_worker
from smello_server.app import create_app

# -- Mock target API server ---------------------------------------------------


class _MockTargetHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"status": "ok", "path": self.path}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)
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
