"""Monkey-patch for the `httpx` library (sync and async)."""

import logging
import time
from urllib.parse import urlparse

from smello.capture import serialize_request_response
from smello.config import SmelloConfig
from smello.transport import send_http

logger = logging.getLogger(__name__)


def patch_httpx(config: SmelloConfig) -> None:
    """Patch httpx.Client.send and httpx.AsyncClient.send."""
    try:
        import httpx  # noqa: PLC0415 -- optional dependency
    except ImportError:
        return  # httpx not installed, skip

    _patch_sync(httpx, config)
    _patch_async(httpx, config)


def _patch_sync(httpx, config: SmelloConfig) -> None:
    original_send = httpx.Client.send

    def patched_send(self, request, **kwargs):
        host = urlparse(str(request.url)).hostname or ""

        if not config.should_capture(host):
            return original_send(self, request, **kwargs)

        start = time.monotonic()
        response = original_send(self, request, **kwargs)
        duration = time.monotonic() - start

        try:
            payload = serialize_request_response(
                config=config,
                method=request.method,
                url=str(request.url),
                request_headers=dict(request.headers),
                request_body=request.content,
                status_code=response.status_code,
                response_headers=dict(response.headers),
                response_body=response.content,
                duration_s=duration,
                library="httpx",
            )
            send_http(payload)
        except Exception as err:
            logger.debug("Failed to capture request: %s", err)

        return response

    httpx.Client.send = patched_send


def _patch_async(httpx, config: SmelloConfig) -> None:
    original_send = httpx.AsyncClient.send

    async def patched_send(self, request, **kwargs):
        host = urlparse(str(request.url)).hostname or ""

        if not config.should_capture(host):
            return await original_send(self, request, **kwargs)

        start = time.monotonic()
        response = await original_send(self, request, **kwargs)
        duration = time.monotonic() - start

        try:
            payload = serialize_request_response(
                config=config,
                method=request.method,
                url=str(request.url),
                request_headers=dict(request.headers),
                request_body=request.content,
                status_code=response.status_code,
                response_headers=dict(response.headers),
                response_body=response.content,
                duration_s=duration,
                library="httpx",
            )
            send_http(payload)
        except Exception as err:
            logger.debug("Failed to capture request: %s", err)

        return response

    httpx.AsyncClient.send = patched_send
