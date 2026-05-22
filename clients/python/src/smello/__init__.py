"""Smello - Capture outgoing HTTP requests, logs, and exceptions automatically."""

import atexit
import logging
from urllib.parse import urlparse

from smello._env import env_bool, env_list, env_log_level, env_str, parse_log_level
from smello.config import SmelloConfig
from smello.patches import apply_all as _apply_all
from smello.transport import flush, shutdown
from smello.transport import start_worker as _start_worker

logger = logging.getLogger("smello")
logger.addHandler(logging.NullHandler())

__all__ = ["init", "flush", "shutdown"]
__version__ = "0.10.2"

DEFAULT_REDACT_HEADERS = ["authorization", "x-api-key"]

_config: SmelloConfig | None = None
_patched: bool = False
_atexit_registered: bool = False


def init(
    server_url: str | None = None,
    capture_hosts: list[str] | None = None,
    capture_all: bool | None = None,
    ignore_hosts: list[str] | None = None,
    redact_headers: list[str] | None = None,
    redact_query_params: list[str] | None = None,
    capture_exceptions: bool | None = None,
    capture_logs: bool | None = None,
    log_level: int | str | None = None,
    ignore_loggers: list[str] | None = None,
) -> None:
    """Initialize Smello. Patches HTTP libraries, logging, and exception hooks.

    Smello only activates when a server URL is provided — either via the
    ``server_url`` parameter or the ``SMELLO_URL`` environment variable.
    Without a URL, ``init()`` is a no-op: no monkey-patching, no background
    threads, no side effects.  This makes it safe to leave ``smello.init()``
    in production code and control activation purely via the environment.

    Each parameter falls back to a ``SMELLO_*`` environment variable when
    not passed explicitly, then to a hardcoded default:

    ====================  ==============================  ==========================
    Parameter             Environment variable            Default
    ====================  ==============================  ==========================
    server_url            ``SMELLO_URL``                  ``None`` (inactive)
    capture_all           ``SMELLO_CAPTURE_ALL``          ``True``
    capture_hosts         ``SMELLO_CAPTURE_HOSTS``        ``[]``
    ignore_hosts          ``SMELLO_IGNORE_HOSTS``         ``[]``
    redact_headers        ``SMELLO_REDACT_HEADERS``       ``["authorization", "x-api-key"]``
    redact_query_params   ``SMELLO_REDACT_QUERY_PARAMS``  ``[]``
    capture_exceptions    ``SMELLO_CAPTURE_EXCEPTIONS``   ``True``
    capture_logs          ``SMELLO_CAPTURE_LOGS``         ``False``
    log_level             ``SMELLO_LOG_LEVEL``            ``30`` (WARNING)
    ignore_loggers        ``SMELLO_IGNORE_LOGGERS``       ``[]``
    ====================  ==============================  ==========================

    ``log_level`` accepts an integer (``10``, ``20``, ``30``) or a standard
    level name (``"DEBUG"``, ``"INFO"``, ``"WARNING"``), case-insensitive.
    The same applies to the ``SMELLO_LOG_LEVEL`` environment variable.

    .. note::

       ``log_level`` is a capture filter, not a logger override. It controls
       which records Smello keeps after they pass through Python's normal
       logging pipeline.  It cannot capture records that the application's
       loggers have already filtered out.  To capture DEBUG-level logs, the
       application must configure its own logging level accordingly (e.g.
       ``logging.basicConfig(level=logging.DEBUG)``).

    Boolean env vars accept ``true``/``1``/``yes`` and ``false``/``0``/``no``
    (case-insensitive).  List env vars are comma-separated.

    Calling ``init()`` more than once is safe. The first call applies the
    monkey-patches; subsequent calls update the live ``SmelloConfig`` in
    place so new args (filtering, redaction) take effect immediately,
    without re-wrapping already patched methods. This makes ``smello run``
    safe to use on programs that already call ``smello.init()`` themselves.
    """
    global _config, _patched, _atexit_registered

    # Resolve: explicit param > env var
    if server_url is None:
        server_url = env_str("URL")
    if not server_url:
        logger.warning(
            "smello.init() called without a server URL. "
            "Set SMELLO_URL or pass server_url= to activate. Doing nothing."
        )
        return

    if capture_all is None:
        env_val = env_bool("CAPTURE_ALL")
        capture_all = env_val if env_val is not None else True

    if capture_hosts is None:
        capture_hosts = env_list("CAPTURE_HOSTS") or []

    if ignore_hosts is None:
        ignore_hosts = env_list("IGNORE_HOSTS") or []

    if redact_headers is None:
        env_headers = env_list("REDACT_HEADERS")
        redact_headers = (
            env_headers if env_headers is not None else list(DEFAULT_REDACT_HEADERS)
        )

    if redact_query_params is None:
        redact_query_params = env_list("REDACT_QUERY_PARAMS") or []

    if capture_exceptions is None:
        env_val = env_bool("CAPTURE_EXCEPTIONS")
        capture_exceptions = env_val if env_val is not None else True

    if capture_logs is None:
        env_val = env_bool("CAPTURE_LOGS")
        capture_logs = env_val if env_val is not None else False

    if ignore_loggers is None:
        ignore_loggers = env_list("IGNORE_LOGGERS") or []

    if log_level is None:
        env_val = env_log_level("LOG_LEVEL")
        log_level = env_val if env_val is not None else logging.WARNING
    elif isinstance(log_level, str):
        parsed = parse_log_level(log_level)
        if parsed is None:
            logger.warning(
                "Unrecognised log_level %r, falling back to WARNING", log_level
            )
            log_level = logging.WARNING
        else:
            log_level = parsed

    resolved_url = server_url.rstrip("/")
    normalized_redact_headers = [h.lower() for h in redact_headers]
    normalized_redact_query_params = [p.lower() for p in redact_query_params]

    if _config is None:
        _config = SmelloConfig(
            server_url=resolved_url,
            capture_hosts=capture_hosts,
            capture_all=capture_all,
            ignore_hosts=ignore_hosts,
            redact_headers=normalized_redact_headers,
            redact_query_params=normalized_redact_query_params,
            capture_exceptions=capture_exceptions,
            capture_logs=capture_logs,
            log_level=log_level,
            ignore_loggers=ignore_loggers,
        )
    else:
        # Mutate in place so closures captured by the existing patches see
        # the new config values without needing to be re-applied.
        _config.server_url = resolved_url
        _config.capture_hosts = capture_hosts
        _config.capture_all = capture_all
        _config.ignore_hosts = ignore_hosts
        _config.redact_headers = normalized_redact_headers
        _config.redact_query_params = normalized_redact_query_params
        _config.capture_exceptions = capture_exceptions
        _config.capture_logs = capture_logs
        _config.log_level = log_level
        _config.ignore_loggers = ignore_loggers

    # Always ignore the smello server itself
    server_host = urlparse(_config.server_url).hostname
    if server_host and server_host not in _config.ignore_hosts:
        _config.ignore_hosts.append(server_host)

    # Start transport worker (idempotent — start_worker guards against re-start)
    _start_worker(_config.server_url)

    # Apply patches once. Re-applying nests wrappers, which would double-capture
    # every request (the second patch's `original_send` is the first patch's
    # patched_send).
    if not _patched:
        _apply_all(_config)
        _patched = True

    # Register atexit hook once so pending captures are flushed on exit
    if not _atexit_registered:
        atexit.register(shutdown)
        _atexit_registered = True
