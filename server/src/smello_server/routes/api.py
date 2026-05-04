"""API routes: typed capture endpoints + JSON read API.

Routes are thin wrappers over `smello_server.services.{capture,events}`.
Per the project convention, route handlers carry the `_api` suffix so they
don't collide with service function names.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from smello_server.services.capture import (
    create_exception_event,
    create_http_event,
    create_log_event,
)
from smello_server.services.events import (
    clear_events,
    get_event,
    get_meta,
    list_events,
)
from smello_server.types import (
    EventDetail,
    EventSummary,
    ExceptionData,
    HttpMeta,
    HttpRequestData,
    HttpResponseData,
    LogData,
    MetaResponse,
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


class CaptureResponse(BaseModel):
    status: str


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
    return await list_events(
        event_type=event_type,
        host=host,
        method=method,
        status=status,
        search=search,
        limit=limit,
    )


@router.get("/events/{event_id}", response_model=EventDetail)
async def get_event_api(event_id: str) -> EventDetail:
    event = await get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.get("/meta", response_model=MetaResponse)
async def get_meta_api() -> MetaResponse:
    return await get_meta()


@router.delete("/events", status_code=204)
async def clear_events_api() -> None:
    await clear_events()
