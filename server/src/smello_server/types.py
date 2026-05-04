"""Shared Pydantic types for captured events.

Two layers:

- **Input** models — what clients POST to `/api/capture/{http,log,exception}`.
  Open (``extra="allow"``) where it matters so older/forward clients can send
  unrecognized fields without rejection.
- **Output** models — what the server stores in ``CapturedEvent.data`` and
  returns from ``/api/events/{id}``. Closed (no extras) so the generated
  TypeScript types are tight. Each carries a ``Literal[...] event_type``
  discriminator and the union ``EventData`` is what the read API exposes.
"""

from datetime import datetime
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, Field, model_validator

# --- Input models (capture endpoints) ---


class HttpRequestData(BaseModel):
    method: str
    url: str
    headers: dict[str, str]
    body: str | None = None
    body_size: int = 0


class HttpResponseData(BaseModel):
    status_code: int
    headers: dict[str, str]
    body: str | None = None
    body_size: int = 0


class HttpMeta(BaseModel):
    library: str = "unknown"
    python_version: str = ""
    smello_version: str = ""


class LogData(BaseModel):
    level: str
    logger_name: str
    message: str
    pathname: str | None = None
    lineno: int | None = None
    func_name: str | None = None
    exc_text: str | None = None
    extra: dict[str, Any] | None = None
    # Allow arbitrary additional fields the client may send.
    model_config = {"extra": "allow"}


class ExceptionFrame(BaseModel):
    filename: str
    lineno: int | None = None
    function: str | None = None
    context_line: str | None = None
    pre_context: list[str] = []
    post_context: list[str] = []


class ExceptionData(BaseModel):
    exc_type: str
    exc_value: str = ""
    exc_module: str | None = None
    traceback_text: str = ""
    frames: list[ExceptionFrame] = []
    model_config = {"extra": "allow"}


# --- Output models (read API + storage) ---


class HttpEventData(BaseModel):
    """HTTP capture as stored and served. Flat by convention."""

    event_type: Literal["http"] = "http"
    duration_ms: int
    method: str
    url: str
    host: str
    request_headers: dict[str, str]
    request_body: str | None = None
    request_body_size: int = 0
    status_code: int
    response_headers: dict[str, str]
    response_body: str | None = None
    response_body_size: int = 0
    library: str = "unknown"
    python_version: str = ""
    smello_version: str = ""


class LogEventData(BaseModel):
    event_type: Literal["log"] = "log"
    level: str
    logger_name: str
    message: str
    pathname: str | None = None
    lineno: int | None = None
    func_name: str | None = None
    exc_text: str | None = None
    extra: dict[str, Any] | None = None


class ExceptionEventData(BaseModel):
    event_type: Literal["exception"] = "exception"
    exc_type: str
    exc_value: str = ""
    exc_module: str | None = None
    traceback_text: str = ""
    frames: list[ExceptionFrame] = []


EventType = Literal["http", "log", "exception"]

EventData = Annotated[
    HttpEventData | LogEventData | ExceptionEventData,
    Field(discriminator="event_type"),
]


# --- API response models ---


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
