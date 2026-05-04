"""Read-side queries for captured events: list, get, meta, clear."""

from typing import Any

from pydantic import TypeAdapter
from tortoise import connections

from smello_server.models import CapturedEvent
from smello_server.types import EventData

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


async def list_events(
    *,
    event_type: str | None = None,
    host: str | None = None,
    method: str | None = None,
    status: int | None = None,
    search: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return event summaries matching the filters, newest first.

    Returns plain dicts with keys: id, timestamp, event_type, summary.
    """
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
            {
                "id": str(r["id"]),
                "timestamp": r["timestamp"],
                "event_type": r["event_type"],
                "summary": r["summary"],
            }
            for r in rows
        ]

    qs = CapturedEvent.all()
    if event_type:
        qs = qs.filter(event_type=event_type)
    events = await qs.limit(limit)
    return [
        {
            "id": str(e.id),
            "timestamp": e.timestamp,
            "event_type": e.event_type,
            "summary": e.summary,
        }
        for e in events
    ]


async def get_event(event_id: str) -> CapturedEvent | None:
    try:
        return await CapturedEvent.get(id=event_id)
    except Exception:
        return None


async def get_meta() -> dict[str, list[str]]:
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

    return {
        "hosts": hosts,
        "methods": methods,
        "event_types": sorted(set(event_types)),
    }


async def clear_events() -> None:
    await CapturedEvent.all().delete()
