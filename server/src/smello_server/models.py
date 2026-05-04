"""Tortoise ORM models for captured events."""

from datetime import datetime, timezone

from tortoise import fields
from tortoise.models import Model


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CapturedEvent(Model):
    id = fields.UUIDField(pk=True)
    timestamp = fields.DatetimeField(default=utcnow)
    event_type = fields.CharField(max_length=16, index=True)  # http, log, exception
    summary = fields.CharField(max_length=500)
    data: dict = fields.JSONField()

    class Meta:
        table = "captured_events"
        ordering = ["-timestamp"]
