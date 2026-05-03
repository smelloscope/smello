"""Persistence for captured events.

Each `create_*` function takes typed Pydantic input, builds the flat `data`
JSON dict and one-line `summary`, and writes a `CapturedEvent` row.
"""

import uuid
from typing import Any
from urllib.parse import urlparse

from smello_server.models import CapturedEvent
from smello_server.types import (
    ExceptionData,
    HttpMeta,
    HttpRequestData,
    HttpResponseData,
    LogData,
)


async def create_http_event(
    *,
    event_id: str | None,
    duration_ms: int,
    request: HttpRequestData,
    response: HttpResponseData,
    meta: HttpMeta,
) -> CapturedEvent:
    host = urlparse(request.url).hostname or "unknown"
    summary = _build_http_summary(request.method, request.url, response.status_code)
    data: dict[str, Any] = {
        "duration_ms": duration_ms,
        "method": request.method.upper(),
        "url": request.url,
        "host": host,
        "request_headers": request.headers,
        "request_body": request.body,
        "request_body_size": request.body_size,
        "status_code": response.status_code,
        "response_headers": response.headers,
        "response_body": response.body,
        "response_body_size": response.body_size,
        "library": meta.library,
    }
    return await CapturedEvent.create(
        id=_resolve_id(event_id),
        event_type="http",
        summary=summary,
        data=data,
    )


def _build_http_summary(method: str, url: str, status_code: int) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    return f"{method.upper()} {path} → {status_code}"


async def create_log_event(*, event_id: str | None, data: LogData) -> CapturedEvent:
    summary = _build_log_summary(data.level, data.logger_name, data.message)
    return await CapturedEvent.create(
        id=_resolve_id(event_id),
        event_type="log",
        summary=summary,
        data=data.model_dump(),
    )


def _build_log_summary(level: str, logger_name: str, message: str) -> str:
    if len(message) > 200:
        message = message[:200] + "…"
    return f"{level} {logger_name}: {message}"


async def create_exception_event(
    *, event_id: str | None, data: ExceptionData
) -> CapturedEvent:
    summary = _build_exception_summary(data.exc_type, data.exc_value)
    return await CapturedEvent.create(
        id=_resolve_id(event_id),
        event_type="exception",
        summary=summary,
        data=data.model_dump(),
    )


def _build_exception_summary(exc_type: str, exc_value: str) -> str:
    if len(exc_value) > 200:
        exc_value = exc_value[:200] + "…"
    return f"{exc_type}: {exc_value}"


def _resolve_id(event_id: str | None) -> str:
    """Shared helper: use the caller-supplied id, or generate a new UUID."""
    return event_id or str(uuid.uuid4())
