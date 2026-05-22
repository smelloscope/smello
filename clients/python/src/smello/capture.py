"""Serialize captured HTTP request/response pairs for sending to the server."""

import time
import uuid

import smello
from smello.config import SmelloConfig
from smello.utils import (
    body_to_str,
    python_version,
    redact_headers,
    redact_query_params,
)


def serialize_request_response(
    *,
    config: SmelloConfig,
    method: str,
    url: str,
    request_headers: dict,
    request_body: str | bytes | None,
    status_code: int,
    response_headers: dict,
    response_body: str | bytes | None,
    duration_s: float,
    library: str,
) -> dict:
    """Build the capture payload dict."""
    req_headers = redact_headers(dict(request_headers), config.redact_headers)
    url = redact_query_params(url, config.redact_query_params)
    resp_headers = dict(response_headers)

    req_body_str = body_to_str(request_body)
    resp_body_str = body_to_str(response_body)

    return {
        "id": str(uuid.uuid4()),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "duration_ms": int(duration_s * 1000),
        "request": {
            "method": method,
            "url": url,
            "headers": req_headers,
            "body": req_body_str,
            "body_size": len(request_body) if request_body else 0,
        },
        "response": {
            "status_code": status_code,
            "headers": resp_headers,
            "body": resp_body_str,
            "body_size": len(response_body) if response_body else 0,
        },
        "meta": {
            "library": library,
            "python_version": python_version(),
            "smello_version": smello.__version__,
        },
    }
