"""FastAPI / Starlette ASGI middleware for capturing incoming HTTP requests."""

import logging
import sys
import time
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

import smello
from smello.patches.patch_excepthook import capture_exception
from smello.transport import send_http_incoming
from smello.utils import (
    body_to_str,
    python_version,
    redact_headers,
    redact_query_params,
)

logger = logging.getLogger(__name__)

MAX_BODY_CAPTURE = 1_048_576  # 1 MB


class SmelloMiddleware:
    """Raw ASGI middleware that captures incoming request/response pairs.

    Usage::

        import smello
        from smello.integrations.fastapi import SmelloMiddleware

        smello.init()
        app = FastAPI()
        app.add_middleware(SmelloMiddleware)
    """

    def __init__(
        self,
        app: Callable[..., Awaitable[Any]],
        ignore_paths: list[str] | None = None,
    ) -> None:
        self.app = app
        self.ignore_paths = ignore_paths or []

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        config = smello._config
        if config is None:
            await self.app(scope, receive, send)
            return

        if self.ignore_paths:
            path = scope.get("path", "/")
            if any(path.startswith(prefix) for prefix in self.ignore_paths):
                await self.app(scope, receive, send)
                return

        start = time.monotonic()

        request_body_chunks: list[bytes] = []
        request_body_size = 0
        request_exceeded = False

        async def receive_wrapper():
            nonlocal request_exceeded, request_body_size
            message = await receive()
            if message["type"] == "http.request":
                body = message.get("body", b"")
                if not request_exceeded:
                    request_body_chunks.append(body)
                    request_body_size += len(body)
                    if request_body_size > MAX_BODY_CAPTURE:
                        request_body_chunks.clear()
                        request_exceeded = True
            return message

        response_status = 0
        response_headers: dict[str, str] = {}
        response_body_chunks: list[bytes] = []
        response_body_size = 0
        response_exceeded = False

        async def send_wrapper(message):
            nonlocal \
                response_status, \
                response_headers, \
                response_exceeded, \
                response_body_size
            if message["type"] == "http.response.start":
                response_status = message["status"]
                raw_headers = message.get("headers", [])
                response_headers = {
                    k.decode("latin-1"): v.decode("latin-1") for k, v in raw_headers
                }
            elif message["type"] == "http.response.body":
                body = message.get("body", b"")
                if not response_exceeded:
                    response_body_chunks.append(body)
                    response_body_size += len(body)
                    if response_body_size > MAX_BODY_CAPTURE:
                        response_body_chunks.clear()
                        response_exceeded = True
            await send(message)

        exc_type_name: str | None = None
        exc_value_str: str | None = None

        try:
            await self.app(scope, receive_wrapper, send_wrapper)
        except Exception as exc:
            exc_type_name = type(exc).__qualname__
            exc_value_str = str(exc)
            capture_exception(*sys.exc_info())
            raise
        finally:
            duration_ms = int((time.monotonic() - start) * 1000)
            _capture(
                config=config,
                scope=scope,
                duration_ms=duration_ms,
                req_body_chunks=request_body_chunks,
                req_body_size=request_body_size,
                req_exceeded=request_exceeded,
                status=response_status,
                resp_headers=response_headers,
                resp_body_chunks=response_body_chunks,
                resp_body_size=response_body_size,
                resp_exceeded=response_exceeded,
                exc_type_name=exc_type_name,
                exc_value_str=exc_value_str,
            )


def _capture(
    *,
    config: Any,
    scope: Any,
    duration_ms: int,
    req_body_chunks: list[bytes],
    req_body_size: int,
    req_exceeded: bool,
    status: int,
    resp_headers: dict[str, str],
    resp_body_chunks: list[bytes],
    resp_body_size: int,
    resp_exceeded: bool,
    exc_type_name: str | None,
    exc_value_str: str | None,
) -> None:
    try:
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/")

        scheme = scope.get("scheme", "http")
        raw_headers = scope.get("headers", [])
        req_headers: dict[str, str] = {}
        host_header = ""
        for k, v in raw_headers:
            name = k.decode("latin-1")
            value = v.decode("latin-1")
            req_headers[name] = value
            if name.lower() == "host":
                host_header = value

        if host_header:
            host_port = host_header
        else:
            server = scope.get("server")
            host_port = f"{server[0]}:{server[1]}" if server else "unknown"

        query_string = scope.get("query_string", b"")
        qs = query_string.decode("latin-1") if query_string else ""
        url = f"{scheme}://{host_port}{path}"
        if qs:
            url += f"?{qs}"
        url = redact_query_params(url, config.redact_query_params)

        req_headers = redact_headers(req_headers, config.redact_headers)
        resp_headers_redacted = redact_headers(resp_headers, config.redact_headers)

        route = None
        route_obj = scope.get("route")
        if route_obj is not None:
            route = getattr(route_obj, "path", None)

        client = scope.get("client")
        client_ip = client[0] if client else None

        if status == 0 and exc_type_name is not None:
            status = 500

        req_body = b"".join(req_body_chunks) if not req_exceeded else None
        resp_body = b"".join(resp_body_chunks) if not resp_exceeded else None

        payload = {
            "id": str(uuid.uuid4()),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "duration_ms": duration_ms,
            "request": {
                "method": method,
                "path": path,
                "url": url,
                "headers": req_headers,
                "body": body_to_str(req_body),
                "body_size": req_body_size,
            },
            "response": {
                "status_code": status,
                "headers": resp_headers_redacted,
                "body": body_to_str(resp_body),
                "body_size": resp_body_size,
            },
            "meta": {
                "framework": "fastapi",
                "route": route,
                "client_ip": client_ip,
                "python_version": python_version(),
                "smello_version": smello.__version__,
                "exc_type": exc_type_name,
                "exc_value": exc_value_str,
            },
        }
        send_http_incoming(payload)
    except Exception as err:
        logger.debug("failed to capture incoming request: %s", err)
