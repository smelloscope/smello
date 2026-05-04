"""Capture Python log records via logging.Logger.callHandlers."""

import logging
import uuid
from datetime import datetime, timezone

from smello import transport
from smello.config import SmelloConfig

_patched = False

# Logger names to ignore to prevent recursion (smello's own loggers
# and urllib3 which is used by the transport).
IGNORED_PREFIXES = ("smello", "urllib3")

# Standard LogRecord attributes — everything else goes into "extra".
STANDARD_ATTRS = frozenset(
    {
        "name",
        "msg",
        "args",
        "created",
        "relativeCreated",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "pathname",
        "filename",
        "module",
        "levelno",
        "levelname",
        "thread",
        "threadName",
        "process",
        "processName",
        "msecs",
        "message",
        "taskName",
    }
)


def patch_logging(config: SmelloConfig) -> None:
    """Monkey-patch logging.Logger.callHandlers to capture log records."""
    global _patched
    if _patched:
        return
    if not config.capture_logs:
        return
    _patched = True

    original_callhandlers = logging.Logger.callHandlers

    def patched_callhandlers(self, record):
        original_callhandlers(self, record)
        try:
            if any(self.name.startswith(p) for p in IGNORED_PREFIXES):
                return
            if record.levelno < config.log_level:
                return
            _capture_log_record(record)
        except Exception:
            pass  # never interfere with logging

    logging.Logger.callHandlers = patched_callhandlers  # type: ignore[assignment]


def _capture_log_record(record: logging.LogRecord) -> None:
    """Serialize and send a log record event."""
    extra = {}
    for key, value in record.__dict__.items():
        if key.startswith("_") or key in STANDARD_ATTRS:
            continue
        try:
            # Quick serializability check
            repr(value)
            extra[key] = value
        except Exception:
            extra[key] = repr(value)

    transport.send_log(
        {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "data": {
                "level": record.levelname,
                "logger_name": record.name,
                "message": record.getMessage(),
                "pathname": record.pathname,
                "lineno": record.lineno,
                "func_name": record.funcName,
                "exc_text": record.exc_text,
                "extra": extra if extra else None,
            },
        }
    )
