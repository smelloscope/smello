"""Tortoise ORM models for captured events."""

from datetime import datetime, timezone

from tortoise import fields
from tortoise.models import Model


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CapturedEvent(Model):
    """A single captured event (HTTP request, log record, or exception).

    Top-level columns (``id``, ``timestamp``, ``event_type``, ``summary``)
    are structural fields needed for ordering, discrimination, and list
    display.  Everything else — including filterable fields like ``host``,
    ``method``, ``app``, ``session`` — lives in the ``data`` JSON blob and
    is queried via ``json_extract()`` when needed.  Keep it simple: add a
    top-level column only when ``json_extract()`` is a proven bottleneck.
    """

    id = fields.UUIDField(pk=True)
    timestamp = fields.DatetimeField(default=utcnow)
    event_type = fields.CharField(max_length=16, db_index=True)
    summary = fields.CharField(max_length=500)
    data: dict = fields.JSONField()

    class Meta:
        table = "captured_events"
        ordering = ["-timestamp"]
