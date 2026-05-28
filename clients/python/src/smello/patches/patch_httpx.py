"""Instrument ``httpx`` via its event hooks system.

Instead of monkey-patching ``Client.send`` / ``AsyncClient.send``, we patch
``Client.__init__`` and ``AsyncClient.__init__`` to inject event hooks — the
same pattern used by the aiohttp patch with ``TraceConfig``.

The ``response`` hook wraps the response byte-stream with a tee that
accumulates chunks and sends the capture when the stream is closed.  This
works uniformly for both streaming and non-streaming requests: httpx always
reads the body through ``response.stream`` and calls ``close()`` afterwards.
"""

import logging
import time
from urllib.parse import urlparse

from smello.capture import serialize_request_response
from smello.config import SmelloConfig
from smello.transport import send_http
from smello.utils import redact_query_params

logger = logging.getLogger(__name__)

MAX_BODY_CAPTURE = 1_048_576  # 1 MB


def patch_httpx(config: SmelloConfig) -> None:
    """Inject event hooks into every httpx Client and AsyncClient."""
    try:
        import httpx  # noqa: PLC0415 -- optional dependency
    except ImportError:
        logger.debug("skipped httpx patch (not installed)")
        return

    _patch_init(httpx.Client, _make_sync_hooks(config))
    _patch_init(httpx.AsyncClient, _make_async_hooks(config))
    logger.debug("patched httpx.Client and httpx.AsyncClient")


# ---------------------------------------------------------------------------
# __init__ patching — inject event hooks into every client
# ---------------------------------------------------------------------------


def _patch_init(client_cls, hooks: dict) -> None:
    original_init = client_cls.__init__

    def patched_init(self, *args, **kwargs):
        event_hooks = dict(kwargs.get("event_hooks") or {})
        for key, new_hooks in hooks.items():
            existing = list(event_hooks.get(key, []))
            existing.extend(new_hooks)
            event_hooks[key] = existing
        kwargs["event_hooks"] = event_hooks
        return original_init(self, *args, **kwargs)

    client_cls.__init__ = patched_init  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Hook factories
# ---------------------------------------------------------------------------

_START_KEY = "_smello_start"


def _make_sync_hooks(config: SmelloConfig) -> dict:
    def on_request(request):
        request.extensions[_START_KEY] = time.monotonic()

    def on_response(response):
        host = urlparse(str(response.request.url)).hostname or ""
        if not config.should_capture(host):
            logger.debug("skipped %s %s (ignored host)", response.request.method, host)
            return
        start = response.request.extensions.pop(_START_KEY, time.monotonic())
        _wrap_sync_stream(response, start, config)

    return {"request": [on_request], "response": [on_response]}


def _make_async_hooks(config: SmelloConfig) -> dict:
    async def on_request(request):
        request.extensions[_START_KEY] = time.monotonic()

    async def on_response(response):
        host = urlparse(str(response.request.url)).hostname or ""
        if not config.should_capture(host):
            logger.debug("skipped %s %s (ignored host)", response.request.method, host)
            return
        start = response.request.extensions.pop(_START_KEY, time.monotonic())
        _wrap_async_stream(response, start, config)

    return {"request": [on_request], "response": [on_response]}


# ---------------------------------------------------------------------------
# Capture helper
# ---------------------------------------------------------------------------


def _send_capture(*, config, request, response, response_body, start):
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
            response_body=response_body,
            duration_s=duration,
            library="httpx",
        )
        send_http(payload)
        logger.debug(
            "captured %s %s via httpx (%d)",
            request.method,
            redact_query_params(str(request.url), config.redact_query_params),
            response.status_code,
        )
    except Exception as err:
        logger.debug("failed to capture request: %s", err)


# ---------------------------------------------------------------------------
# Stream wrappers — tee bytes and capture on close
# ---------------------------------------------------------------------------


def _wrap_sync_stream(response, start, config):
    import httpx  # noqa: PLC0415

    original_stream = response.stream
    chunks: list[bytes] = []
    exceeded = False
    sent = False

    class _TeeStream(httpx.SyncByteStream):
        def __iter__(self):
            nonlocal exceeded
            for chunk in original_stream:
                if not exceeded:
                    chunks.append(chunk)
                    if sum(len(c) for c in chunks) > MAX_BODY_CAPTURE:
                        chunks.clear()
                        exceeded = True
                yield chunk

        def close(self):
            nonlocal sent
            if not sent:
                sent = True
                body = b"".join(chunks) if not exceeded else None
                _send_capture(
                    config=config,
                    request=response.request,
                    response=response,
                    response_body=body,
                    start=start,
                )
            original_stream.close()

    response.stream = _TeeStream()


def _wrap_async_stream(response, start, config):
    import httpx  # noqa: PLC0415

    original_stream = response.stream
    chunks: list[bytes] = []
    exceeded = False
    sent = False

    class _TeeStream(httpx.AsyncByteStream):
        async def __aiter__(self):
            nonlocal exceeded
            async for chunk in original_stream:
                if not exceeded:
                    chunks.append(chunk)
                    if sum(len(c) for c in chunks) > MAX_BODY_CAPTURE:
                        chunks.clear()
                        exceeded = True
                yield chunk

        async def aclose(self):
            nonlocal sent
            if not sent:
                sent = True
                body = b"".join(chunks) if not exceeded else None
                _send_capture(
                    config=config,
                    request=response.request,
                    response=response,
                    response_body=body,
                    start=start,
                )
            await original_stream.aclose()

    response.stream = _TeeStream()
