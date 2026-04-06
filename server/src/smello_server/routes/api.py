"""API routes: ingestion endpoint and JSON API."""

import uuid
from datetime import datetime
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from tortoise import connections

from smello_server.models import CapturedRequest

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
    id: str | None = None
    timestamp: str | None = None
    duration_ms: int = 0
    request: RequestData
    response: ResponseData
    meta: MetaData = MetaData()


# --- Output models ---


class CaptureResponse(BaseModel):
    status: str


class RequestSummary(BaseModel):
    id: str
    timestamp: datetime
    method: str
    url: str
    host: str
    status_code: int
    duration_ms: int


class RequestDetail(RequestSummary):
    library: str
    request_headers: dict[str, str]
    request_body: str | None
    request_body_size: int
    response_headers: dict[str, str]
    response_body: str | None
    response_body_size: int


class MetaResponse(BaseModel):
    hosts: list[str]
    methods: list[str]


# --- Routes ---


@router.post("/capture", status_code=201, response_model=CaptureResponse)
async def capture(payload: CapturePayload) -> CaptureResponse:
    host = urlparse(payload.request.url).hostname or "unknown"

    await CapturedRequest.create(
        id=payload.id or uuid.uuid4(),
        duration_ms=payload.duration_ms,
        method=payload.request.method.upper(),
        url=payload.request.url,
        request_headers=payload.request.headers,
        request_body=payload.request.body,
        request_body_size=payload.request.body_size,
        status_code=payload.response.status_code,
        response_headers=payload.response.headers,
        response_body=payload.response.body,
        response_body_size=payload.response.body_size,
        host=host,
        library=payload.meta.library,
    )
    return CaptureResponse(status="ok")


@router.get("/requests", response_model=list[RequestSummary])
async def list_requests(
    host: str | None = Query(None),
    method: str | None = Query(None),
    status: int | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, le=200),
) -> list[RequestSummary]:
    if search:
        # Tortoise ORM's JSONField doesn't support __icontains, so use raw
        # SQL to search across all columns including JSON header fields.
        where_parts: list[str] = []
        params: list[str | int] = []

        if host:
            where_parts.append("host = ?")
            params.append(host)
        if method:
            where_parts.append("method = ?")
            params.append(method.upper())
        if status:
            where_parts.append("status_code = ?")
            params.append(status)

        like_pattern = f"%{search}%"
        where_parts.append(
            "(url LIKE ? COLLATE NOCASE"
            " OR host LIKE ? COLLATE NOCASE"
            " OR method LIKE ? COLLATE NOCASE"
            " OR request_headers LIKE ? COLLATE NOCASE"
            " OR request_body LIKE ? COLLATE NOCASE"
            " OR response_headers LIKE ? COLLATE NOCASE"
            " OR response_body LIKE ? COLLATE NOCASE)"
        )
        params.extend([like_pattern] * 7)

        where_clause = " AND ".join(where_parts)
        db = connections.get("default")
        _, rows = await db.execute_query(
            f"SELECT id, timestamp, method, url, host, status_code, duration_ms"
            f" FROM captured_requests WHERE {where_clause}"
            " ORDER BY timestamp DESC LIMIT ?",
            [*params, limit],
        )
        return [
            RequestSummary(
                id=str(r["id"]),
                timestamp=datetime.fromisoformat(r["timestamp"]),
                method=r["method"],
                url=r["url"],
                host=r["host"],
                status_code=r["status_code"],
                duration_ms=r["duration_ms"],
            )
            for r in rows
        ]

    qs = CapturedRequest.all()
    if host:
        qs = qs.filter(host=host)
    if method:
        qs = qs.filter(method=method.upper())
    if status:
        qs = qs.filter(status_code=status)
    requests = await qs.limit(limit)
    return [
        RequestSummary(
            id=str(r.id),
            timestamp=r.timestamp,
            method=r.method,
            url=r.url,
            host=r.host,
            status_code=r.status_code,
            duration_ms=r.duration_ms,
        )
        for r in requests
    ]


@router.get("/requests/{request_id}", response_model=RequestDetail)
async def get_request(request_id: str) -> RequestDetail:
    try:
        r = await CapturedRequest.get(id=request_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Request not found")

    return RequestDetail(
        id=str(r.id),
        timestamp=r.timestamp,
        method=r.method,
        url=r.url,
        host=r.host,
        status_code=r.status_code,
        duration_ms=r.duration_ms,
        library=r.library,
        request_headers=r.request_headers,
        request_body=r.request_body,
        request_body_size=r.request_body_size,
        response_headers=r.response_headers,
        response_body=r.response_body,
        response_body_size=r.response_body_size,
    )


@router.get("/meta", response_model=MetaResponse)
async def get_meta() -> MetaResponse:
    hosts: list[str] = (
        await CapturedRequest.all().distinct().values_list("host", flat=True)
    )  # type: ignore[assignment]
    methods: list[str] = (
        await CapturedRequest.all().distinct().values_list("method", flat=True)
    )  # type: ignore[assignment]
    return MetaResponse(hosts=sorted(set(hosts)), methods=sorted(set(methods)))


@router.delete("/requests", status_code=204)
async def clear_requests() -> None:
    await CapturedRequest.all().delete()
