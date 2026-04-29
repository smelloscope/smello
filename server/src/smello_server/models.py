"""Tortoise ORM models for captured events."""

from tortoise import fields
from tortoise.models import Model


class CapturedEvent(Model):
    id = fields.UUIDField(pk=True)
    timestamp = fields.DatetimeField(auto_now_add=True)
    event_type = fields.CharField(max_length=16, index=True)  # http, log, exception
    summary = fields.CharField(max_length=500)
    data: dict = fields.JSONField()

    class Meta:
        table = "captured_events"
        ordering = ["-timestamp"]
