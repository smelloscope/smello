"""Smello - Capture outgoing HTTP requests automatically."""

import atexit
import logging

from smello.config import SmelloConfig

logging.getLogger("smello").addHandler(logging.NullHandler())

__version__ = "0.2.0"

_config: SmelloConfig | None = None
_atexit_registered: bool = False


def init(
    server_url: str = "http://localhost:5110",
    capture_hosts: list[str] | None = None,
    capture_all: bool = True,
    ignore_hosts: list[str] | None = None,
    redact_headers: list[str] | None = None,
    enabled: bool = True,
) -> None:
    """Initialize Smello. Patches requests and httpx to capture outgoing HTTP traffic."""
    global _config, _atexit_registered

    if not enabled:
        return

    _config = SmelloConfig(
        server_url=server_url.rstrip("/"),
        capture_hosts=capture_hosts or [],
        capture_all=capture_all,
        ignore_hosts=ignore_hosts or [],
        redact_headers=[
            h.lower() for h in (redact_headers or ["authorization", "x-api-key"])
        ],
    )

    # Always ignore the smello server itself
    from urllib.parse import urlparse

    server_host = urlparse(_config.server_url).hostname
    if server_host and server_host not in _config.ignore_hosts:
        _config.ignore_hosts.append(server_host)

    # Start transport worker
    from smello.transport import start_worker

    start_worker(_config.server_url)

    # Apply patches
    from smello.patches import apply_all

    apply_all(_config)

    # Register atexit hook once so pending captures are flushed on exit
    if not _atexit_registered:
        atexit.register(shutdown)
        _atexit_registered = True


def flush(timeout: float = 2.0) -> bool:
    """Block until all pending captures are sent, or *timeout* seconds elapse.

    Returns ``True`` if the queue drained in time, ``False`` otherwise.
    """
    from smello.transport import flush as _flush

    return _flush(timeout=timeout)


def shutdown(timeout: float = 2.0) -> bool:
    """Flush pending captures then stop the transport.

    Called automatically via ``atexit`` when ``smello.init()`` has been used.
    Returns ``True`` if the queue drained in time, ``False`` otherwise.
    """
    from smello.transport import shutdown as _shutdown

    return _shutdown(timeout=timeout)
