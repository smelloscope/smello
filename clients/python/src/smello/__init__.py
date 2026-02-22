"""Smello - Capture outgoing HTTP requests automatically."""

import atexit
import logging
from urllib.parse import urlparse

from smello._env import _env_bool, _env_list, _env_str
from smello.config import SmelloConfig
from smello.patches import apply_all as _apply_all
from smello.transport import flush, shutdown
from smello.transport import start_worker as _start_worker

logger = logging.getLogger("smello")
logger.addHandler(logging.NullHandler())

__all__ = ["init", "flush", "shutdown"]
__version__ = "0.3.1"

_DEFAULT_REDACT_HEADERS = ["authorization", "x-api-key"]

_config: SmelloConfig | None = None
_atexit_registered: bool = False


def init(
    server_url: str | None = None,
    capture_hosts: list[str] | None = None,
    capture_all: bool | None = None,
    ignore_hosts: list[str] | None = None,
    redact_headers: list[str] | None = None,
) -> None:
    """Initialize Smello. Patches requests and httpx to capture outgoing HTTP traffic.

    Smello only activates when a server URL is provided — either via the
    ``server_url`` parameter or the ``SMELLO_URL`` environment variable.
    Without a URL, ``init()`` is a no-op: no monkey-patching, no background
    threads, no side effects.  This makes it safe to leave ``smello.init()``
    in production code and control activation purely via the environment.

    Each parameter falls back to a ``SMELLO_*`` environment variable when
    not passed explicitly, then to a hardcoded default:

    ================  ==========================  ==========================
    Parameter         Environment variable        Default
    ================  ==========================  ==========================
    server_url        ``SMELLO_URL``              ``None`` (inactive)
    capture_all       ``SMELLO_CAPTURE_ALL``      ``True``
    capture_hosts     ``SMELLO_CAPTURE_HOSTS``    ``[]``
    ignore_hosts      ``SMELLO_IGNORE_HOSTS``     ``[]``
    redact_headers    ``SMELLO_REDACT_HEADERS``   ``["authorization", "x-api-key"]``
    ================  ==========================  ==========================

    Boolean env vars accept ``true``/``1``/``yes`` and ``false``/``0``/``no``
    (case-insensitive).  List env vars are comma-separated.
    """
    global _config, _atexit_registered

    # Resolve: explicit param > env var
    if server_url is None:
        server_url = _env_str("URL")
    if not server_url:
        logger.warning(
            "smello.init() called without a server URL. "
            "Set SMELLO_URL or pass server_url= to activate. Doing nothing."
        )
        return

    if capture_all is None:
        env_val = _env_bool("CAPTURE_ALL")
        capture_all = env_val if env_val is not None else True

    if capture_hosts is None:
        capture_hosts = _env_list("CAPTURE_HOSTS") or []

    if ignore_hosts is None:
        ignore_hosts = _env_list("IGNORE_HOSTS") or []

    if redact_headers is None:
        env_headers = _env_list("REDACT_HEADERS")
        redact_headers = (
            env_headers if env_headers is not None else list(_DEFAULT_REDACT_HEADERS)
        )

    _config = SmelloConfig(
        server_url=server_url.rstrip("/"),
        capture_hosts=capture_hosts,
        capture_all=capture_all,
        ignore_hosts=ignore_hosts,
        redact_headers=[h.lower() for h in redact_headers],
    )

    # Always ignore the smello server itself
    server_host = urlparse(_config.server_url).hostname
    if server_host and server_host not in _config.ignore_hosts:
        _config.ignore_hosts.append(server_host)

    # Start transport worker
    _start_worker(_config.server_url)

    # Apply patches
    _apply_all(_config)

    # Register atexit hook once so pending captures are flushed on exit
    if not _atexit_registered:
        atexit.register(shutdown)
        _atexit_registered = True
