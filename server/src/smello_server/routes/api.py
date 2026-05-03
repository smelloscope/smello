"""API routes: ingestion endpoint and JSON API."""

import uuid
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from tortoise import connections

from smello_server.models import CapturedEvent

router = APIRouter(prefix="/api")


# --- Input models ---


class RequestData(BaseModel):
    method: str
    url: str
    headers: dict[str, str]
    body: str | None = None
    body_size: int = 0


class ResponseData(BaseModel):
    status_code: int
    headers: dict[str, str]
    body: str | None = None
    body_size: int = 0


class MetaData(BaseModel):
    library: str = "unknown"
    python_version: str = ""
    smello_version: str = ""


class CapturePayload(BaseModel):
    """Flexible capture payload that supports all event types.

    For HTTP events (event_type omitted or "http"), the legacy fields
    (request, response, meta, duration_ms) are used.

    For log/exception events, event_type + data are used.
    """

    event_type: str | None = None
    id: str | None = None
    timestamp: str | None = None

    # HTTP-specific (legacy format)
    duration_ms: int = 0
    request: RequestData | None = None
    response: ResponseData | None = None
    meta: MetaData | None = None

    # Generic event data (for log/exception)
    data: dict[str, Any] | None = None


# --- Output models ---


class CaptureResponse(BaseModel):
    status: str


class EventSummary(BaseModel):
    id: str
    timestamp: datetime
    event_type: str
    summary: str


class EventDetail(EventSummary):
    data: dict[str, Any]


class MetaResponse(BaseModel):
    hosts: list[str]
    methods: list[str]
    event_types: list[str]


# --- Helpers ---


def _build_http_summary(method: str, url: str, status_code: int) -> str:
    """Build a one-line summary for an HTTP event."""
    parsed = urlparse(url)
    path = parsed.path or "/"
    return f"{method.upper()} {path} → {status_code}"


def _build_log_summary(data: dict) -> str:
    """Build a one-line summary for a log event."""
    level = data.get("level", "INFO")
    logger_name = data.get("logger_name", "root")
    message = data.get("message", "")
    if len(message) > 200:
        message = message[:200] + "…"
    return f"{level} {logger_name}: {message}"


def _build_exception_summary(data: dict) -> str:
    """Build a one-line summary for an exception event."""
    exc_type = data.get("exc_type", "Exception")
    exc_value = data.get("exc_value", "")
    if len(exc_value) > 200:
        exc_value = exc_value[:200] + "…"
    return f"{exc_type}: {exc_value}"


# --- Routes ---


@router.post("/capture", status_code=201, response_model=CaptureResponse)
async def capture(payload: CapturePayload) -> CaptureResponse:
    event_type = payload.event_type or "http"
    event_id = payload.id or str(uuid.uuid4())

    if event_type == "http":
        if not payload.request or not payload.response:
            raise HTTPException(
                status_code=422,
                detail="HTTP events require 'request' and 'response' fields",
            )
        meta = payload.meta or MetaData()
        host = urlparse(payload.request.url).hostname or "unknown"
        summary = _build_http_summary(
            payload.request.method,
            payload.request.url,
            payload.response.status_code,
        )
        data = {
            "duration_ms": payload.duration_ms,
            "method": payload.request.method.upper(),
            "url": payload.request.url,
            "host": host,
            "request_headers": payload.request.headers,
            "request_body": payload.request.body,
            "request_body_size": payload.request.body_size,
            "status_code": payload.response.status_code,
            "response_headers": payload.response.headers,
            "response_body": payload.response.body,
            "response_body_size": payload.response.body_size,
            "library": meta.library,
        }
    elif event_type == "log":
        if not payload.data:
            raise HTTPException(
                status_code=422, detail="Log events require a 'data' field"
            )
        summary = _build_log_summary(payload.data)
        data = payload.data
    elif event_type == "exception":
        if not payload.data:
            raise HTTPException(
                status_code=422, detail="Exception events require a 'data' field"
            )
        summary = _build_exception_summary(payload.data)
        data = payload.data
    else:
        raise HTTPException(status_code=422, detail=f"Unknown event_type: {event_type}")

    await CapturedEvent.create(
        id=event_id,
        event_type=event_type,
        summary=summary,
        data=data,
    )
    return CaptureResponse(status="ok")


@router.get("/events", response_model=list[EventSummary])
async def list_events(
    event_type: str | None = Query(None),
    host: str | None = Query(None),
    method: str | None = Query(None),
    status: int | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, le=200),
) -> list[EventSummary]:
    if search or host or method or status:
        where_parts: list[str] = []
        params: list[str | int] = []

        if event_type:
            where_parts.append("event_type = ?")
            params.append(event_type)
        if host:
            where_parts.append("json_extract(data, '$.host') = ?")
            params.append(host)
        if method:
            where_parts.append("json_extract(data, '$.method') = ?")
            params.append(method.upper())
        if status:
            where_parts.append("json_extract(data, '$.status_code') = ?")
            params.append(status)

        if search:
            like_pattern = f"%{search}%"
            where_parts.append(
                "(summary LIKE ? COLLATE NOCASE OR data LIKE ? COLLATE NOCASE)"
            )
            params.extend([like_pattern, like_pattern])

        where_clause = " AND ".join(where_parts) if where_parts else "1=1"
        db = connections.get("default")
        _, rows = await db.execute_query(
            f"SELECT id, timestamp, event_type, summary"
            f" FROM captured_events WHERE {where_clause}"
            " ORDER BY timestamp DESC LIMIT ?",
            [*params, limit],
        )
        return [
            EventSummary(
                id=str(r["id"]),
                timestamp=datetime.fromisoformat(r["timestamp"]),
                event_type=r["event_type"],
                summary=r["summary"],
            )
            for r in rows
        ]

    qs = CapturedEvent.all()
    if event_type:
        qs = qs.filter(event_type=event_type)
    events = await qs.limit(limit)
    return [
        EventSummary(
            id=str(e.id),
            timestamp=e.timestamp,
            event_type=e.event_type,
            summary=e.summary,
        )
        for e in events
    ]


@router.get("/events/{event_id}", response_model=EventDetail)
async def get_event(event_id: str) -> EventDetail:
    try:
        e = await CapturedEvent.get(id=event_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Event not found")

    return EventDetail(
        id=str(e.id),
        timestamp=e.timestamp,
        event_type=e.event_type,
        summary=e.summary,
        data=e.data,
    )


@router.get("/meta", response_model=MetaResponse)
async def get_meta() -> MetaResponse:
    db = connections.get("default")

    _, host_rows = await db.execute_query(
        "SELECT DISTINCT json_extract(data, '$.host') as host"
        " FROM captured_events WHERE event_type = 'http' AND host IS NOT NULL"
    )
    hosts = sorted({r["host"] for r in host_rows if r["host"]})

    _, method_rows = await db.execute_query(
        "SELECT DISTINCT json_extract(data, '$.method') as method"
        " FROM captured_events WHERE event_type = 'http' AND method IS NOT NULL"
    )
    methods = sorted({r["method"] for r in method_rows if r["method"]})

    event_types: list[str] = (
        await CapturedEvent.all().distinct().values_list("event_type", flat=True)
    )  # type: ignore[assignment]

    return MetaResponse(
        hosts=hosts,
        methods=methods,
        event_types=sorted(set(event_types)),
    )


@router.delete("/events", status_code=204)
async def clear_events() -> None:
    await CapturedEvent.all().delete()
