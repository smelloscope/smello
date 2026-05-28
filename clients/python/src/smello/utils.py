"""Shared utilities used by capture modules and integrations."""

import sys
import zlib
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

MAX_DECOMPRESSED = 1_048_576  # 1 MB — matches MAX_BODY_CAPTURE in patches


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
            return _try_decompress_utf8(body) or f"[binary: {len(body)} bytes]"
    return body


def _try_decompress_utf8(body: bytes) -> str | None:
    """Try common HTTP compression formats and return decoded text, or None."""
    # wbits: MAX_WBITS|16 = gzip, MAX_WBITS = zlib-wrapped, negative = raw deflate
    # Brotli is intentionally excluded: the brotli library has no bounded
    # decompression API, so a malicious server could cause unbounded memory
    # allocation. Brotli is near-zero for API traffic anyway.
    for wbits in (zlib.MAX_WBITS | 16, zlib.MAX_WBITS, -zlib.MAX_WBITS):
        result = _safe_zlib_decompress(body, wbits)
        if result is not None:
            try:
                return result.decode("utf-8")
            except UnicodeDecodeError:
                return None
    return None


def _safe_zlib_decompress(body: bytes, wbits: int) -> bytes | None:
    """Decompress with a size cap to protect against zip bombs."""
    obj = zlib.decompressobj(wbits)
    try:
        result = obj.decompress(body, MAX_DECOMPRESSED + 1)
    except zlib.error:
        return None
    if len(result) > MAX_DECOMPRESSED or not obj.eof:
        return None
    return result


def python_version() -> str:
    """Return the running Python version as ``'major.minor.micro'``."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
