"""Read-side queries for captured events: list, get, meta, clear."""

import uuid
from datetime import datetime
from typing import Any, cast

from pydantic import TypeAdapter
from tortoise import connections

from smello_server.models import CapturedEvent
from smello_server.types import (
    EventData,
    EventDetail,
    EventSummary,
    EventType,
    MetaResponse,
)

_event_data_adapter: TypeAdapter[EventData] = TypeAdapter(EventData)


def hydrate_event_data(event_type: str, data: dict[str, Any]) -> EventData:
    """Validate a stored ``data`` blob against the typed ``EventData`` union.

    Injects ``event_type`` from the column into ``data`` if missing, so rows
    written before the typed-output refactor still round-trip without a
    migration. New writes already include ``event_type`` inside ``data``.
    """
    if "event_type" not in data:
        data = {**data, "event_type": event_type}
    return _event_data_adapter.validate_python(data)


def _coerce_timestamp(value: datetime | str) -> datetime:
    return datetime.fromisoformat(value) if isinstance(value, str) else value


async def list_events(
    *,
    event_type: str | None = None,
    host: str | None = None,
    method: str | None = None,
    status: int | None = None,
    search: str | None = None,
    limit: int = 50,
) -> list[EventSummary]:
    """Return event summaries matching the filters, newest first."""
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
                timestamp=_coerce_timestamp(r["timestamp"]),
                event_type=cast(EventType, r["event_type"]),
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
            event_type=cast(EventType, e.event_type),
            summary=e.summary,
        )
        for e in events
    ]


async def get_event(event_id: str) -> EventDetail | None:
    """Return the typed event detail, or None if the id is invalid/missing."""
    try:
        uuid.UUID(event_id)
    except ValueError:
        return None
    event = await CapturedEvent.get_or_none(id=event_id)
    if event is None:
        return None
    return EventDetail(
        id=str(event.id),
        timestamp=event.timestamp,
        event_type=cast(EventType, event.event_type),
        summary=event.summary,
        data=hydrate_event_data(event.event_type, event.data),
    )


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
        event_types=sorted({cast(EventType, t) for t in event_types}),
    )


async def clear_events() -> None:
    await CapturedEvent.all().delete()
