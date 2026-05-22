"""Shared utilities used by capture modules and integrations."""

import sys
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit


def redact_headers(headers: dict, redact_keys: list[str]) -> dict:
    """Replace header values with ``[REDACTED]`` for keys in *redact_keys* (case-insensitive)."""
    return {
        k: ("[REDACTED]" if k.lower() in redact_keys else v) for k, v in headers.items()
    }


def redact_query_params(url: str, redact_keys: list[str]) -> str:
    """Replace query parameter values with ``[REDACTED]`` for keys in *redact_keys* (case-insensitive)."""
    if not redact_keys:
        return url
    parts = urlsplit(url)
    if not parts.query:
        return url
    params = parse_qs(parts.query, keep_blank_values=True)
    redacted = {
        k: (["[REDACTED]"] * len(v) if k.lower() in redact_keys else v)
        for k, v in params.items()
    }
    new_query = urlencode(redacted, doseq=True)
    return urlunsplit(parts._replace(query=new_query))


def body_to_str(body: str | bytes | None) -> str | None:
    """Convert a request/response body to a string, or ``None`` if absent."""
    if body is None:
        return None
    if isinstance(body, bytes):
        try:
            return body.decode("utf-8")
        except UnicodeDecodeError:
            return f"[binary: {len(body)} bytes]"
    return body


def python_version() -> str:
    """Return the running Python version as ``'major.minor.micro'``."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
