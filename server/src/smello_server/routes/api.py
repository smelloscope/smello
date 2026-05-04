"""API routes: typed capture endpoints + JSON read API.

Routes are thin wrappers over `smello_server.services.{capture,events}`.
Per the project convention, route handlers carry the `_api` suffix so they
don't collide with service function names.
"""

from datetime import datetime
from typing import Self, cast

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, model_validator

from smello_server.services.capture import (
    create_exception_event,
    create_http_event,
    create_log_event,
)
from smello_server.services.events import (
    clear_events,
    get_event,
    get_meta,
    hydrate_event_data,
    list_events,
)
from smello_server.types import (
    EventData,
    EventType,
    ExceptionData,
    HttpMeta,
    HttpRequestData,
    HttpResponseData,
    LogData,
)

router = APIRouter(prefix="/api")


# --- Capture payloads (per event type) ---


class HttpCapturePayload(BaseModel):
    id: str | None = None
    timestamp: str | None = None
    duration_ms: int = 0
    request: HttpRequestData
    response: HttpResponseData
    meta: HttpMeta = HttpMeta()


class LogCapturePayload(BaseModel):
    id: str | None = None
    timestamp: str | None = None
    data: LogData


class ExceptionCapturePayload(BaseModel):
    id: str | None = None
    timestamp: str | None = None
    data: ExceptionData


# --- Response models ---


class CaptureResponse(BaseModel):
    status: str


class EventSummary(BaseModel):
    id: str
    timestamp: datetime
    event_type: EventType
    summary: str


class EventDetail(EventSummary):
    data: EventData

    @model_validator(mode="after")
    def _check_event_type_consistency(self) -> Self:
        if self.event_type != self.data.event_type:
            raise ValueError(
                f"event_type mismatch: outer={self.event_type!r},"
                f" data={self.data.event_type!r}"
            )
        return self


class MetaResponse(BaseModel):
    hosts: list[str]
    methods: list[str]
    event_types: list[EventType]


OK = CaptureResponse(status="ok")


# --- Capture routes ---


@router.post("/capture/http", status_code=201, response_model=CaptureResponse)
async def capture_http_api(payload: HttpCapturePayload) -> CaptureResponse:
    await create_http_event(
        event_id=payload.id,
        duration_ms=payload.duration_ms,
        request=payload.request,
        response=payload.response,
        meta=payload.meta,
    )
    return OK


@router.post("/capture/log", status_code=201, response_model=CaptureResponse)
async def capture_log_api(payload: LogCapturePayload) -> CaptureResponse:
    await create_log_event(event_id=payload.id, data=payload.data)
    return OK


@router.post("/capture/exception", status_code=201, response_model=CaptureResponse)
async def capture_exception_api(payload: ExceptionCapturePayload) -> CaptureResponse:
    await create_exception_event(event_id=payload.id, data=payload.data)
    return OK


@router.post(
    "/capture",
    status_code=201,
    response_model=CaptureResponse,
    deprecated=True,
    summary="Deprecated: use /api/capture/http",
)
async def capture_legacy_api(payload: HttpCapturePayload) -> CaptureResponse:
    """Deprecated HTTP capture endpoint.

    Kept for backwards compatibility with old smello client wheels in the wild,
    which only ever posted HTTP captures here. New clients should use the
    typed endpoints `/api/capture/http`, `/api/capture/log`,
    `/api/capture/exception`.
    """
    return await capture_http_api(payload)


# --- Read routes ---


@router.get("/events", response_model=list[EventSummary])
async def list_events_api(
    event_type: str | None = Query(None),
    host: str | None = Query(None),
    method: str | None = Query(None),
    status: int | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, le=200),
) -> list[EventSummary]:
    rows = await list_events(
        event_type=event_type,
        host=host,
        method=method,
        status=status,
        search=search,
        limit=limit,
    )
    return [
        EventSummary(
            id=r["id"],
            timestamp=(
                datetime.fromisoformat(r["timestamp"])
                if isinstance(r["timestamp"], str)
                else r["timestamp"]
            ),
            event_type=cast(EventType, r["event_type"]),
            summary=r["summary"],
        )
        for r in rows
    ]


@router.get("/events/{event_id}", response_model=EventDetail)
async def get_event_api(event_id: str) -> EventDetail:
    event = await get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return EventDetail(
        id=str(event.id),
        timestamp=event.timestamp,
        event_type=cast(EventType, event.event_type),
        summary=event.summary,
        data=hydrate_event_data(event.event_type, event.data),
    )


@router.get("/meta", response_model=MetaResponse)
async def get_meta_api() -> MetaResponse:
    meta = await get_meta()
    return MetaResponse.model_validate(meta)


@router.delete("/events", status_code=204)
async def clear_events_api() -> None:
    await clear_events()
