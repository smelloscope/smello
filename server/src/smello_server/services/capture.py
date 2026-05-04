"""Persistence for captured events.

Each ``create_*`` function takes typed input, builds the typed output model
(`HttpEventData` / `LogEventData` / `ExceptionEventData`) and a one-line
``summary``, then writes a `CapturedEvent` row with the output model dumped to
JSON in the ``data`` column.
"""

import uuid
from datetime import datetime
from urllib.parse import urlparse

from smello_server.models import CapturedEvent, utcnow
from smello_server.types import (
    ExceptionData,
    ExceptionEventData,
    HttpEventData,
    HttpMeta,
    HttpRequestData,
    HttpResponseData,
    LogData,
    LogEventData,
)


async def create_http_event(
    *,
    event_id: str | None,
    timestamp: datetime | None = None,
    duration_ms: int,
    request: HttpRequestData,
    response: HttpResponseData,
    meta: HttpMeta,
) -> CapturedEvent:
    host = urlparse(request.url).hostname or "unknown"
    summary = _build_http_summary(request.method, request.url, response.status_code)
    event_data = HttpEventData(
        duration_ms=duration_ms,
        method=request.method.upper(),
        url=request.url,
        host=host,
        request_headers=request.headers,
        request_body=request.body,
        request_body_size=request.body_size,
        status_code=response.status_code,
        response_headers=response.headers,
        response_body=response.body,
        response_body_size=response.body_size,
        library=meta.library,
        python_version=meta.python_version,
        smello_version=meta.smello_version,
    )
    return await CapturedEvent.create(
        id=_resolve_id(event_id),
        timestamp=timestamp or utcnow(),
        event_type="http",
        summary=summary,
        data=event_data.model_dump(mode="json"),
    )


def _build_http_summary(method: str, url: str, status_code: int) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    return f"{method.upper()} {path} → {status_code}"


async def create_log_event(
    *,
    event_id: str | None,
    timestamp: datetime | None = None,
    data: LogData,
) -> CapturedEvent:
    summary = _build_log_summary(data.level, data.logger_name, data.message)
    event_data = LogEventData(
        level=data.level,
        logger_name=data.logger_name,
        message=data.message,
        pathname=data.pathname,
        lineno=data.lineno,
        func_name=data.func_name,
        exc_text=data.exc_text,
        extra=data.extra,
    )
    return await CapturedEvent.create(
        id=_resolve_id(event_id),
        timestamp=timestamp or utcnow(),
        event_type="log",
        summary=summary,
        data=event_data.model_dump(mode="json"),
    )


def _build_log_summary(level: str, logger_name: str, message: str) -> str:
    if len(message) > 200:
        message = message[:200] + "…"
    return f"{level} {logger_name}: {message}"


async def create_exception_event(
    *,
    event_id: str | None,
    timestamp: datetime | None = None,
    data: ExceptionData,
) -> CapturedEvent:
    summary = _build_exception_summary(data.exc_type, data.exc_value)
    event_data = ExceptionEventData(
        exc_type=data.exc_type,
        exc_value=data.exc_value,
        exc_module=data.exc_module,
        traceback_text=data.traceback_text,
        frames=data.frames,
    )
    return await CapturedEvent.create(
        id=_resolve_id(event_id),
        timestamp=timestamp or utcnow(),
        event_type="exception",
        summary=summary,
        data=event_data.model_dump(mode="json"),
    )


def _build_exception_summary(exc_type: str, exc_value: str) -> str:
    if len(exc_value) > 200:
        exc_value = exc_value[:200] + "…"
    return f"{exc_type}: {exc_value}"


def _resolve_id(event_id: str | None) -> str:
    """Shared helper: use the caller-supplied id, or generate a new UUID."""
    return event_id or str(uuid.uuid4())
