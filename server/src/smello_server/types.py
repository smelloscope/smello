"""Shared Pydantic types for captured events.

Used by `services.capture` (writes) and `routes.api` (request payloads).
Route-only response models stay in `routes/api.py`.
"""

from typing import Any

from pydantic import BaseModel


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
