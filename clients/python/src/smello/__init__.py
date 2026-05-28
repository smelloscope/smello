"""Smello - Capture outgoing HTTP requests, logs, and exceptions automatically."""

import atexit
import json
import logging
import os
from urllib.parse import urlparse

from smello._debug import (
    check_connectivity,
    log_resolved_config,
    setup_debug_logging,
    teardown_debug_logging,
)
from smello._env import env_bool, env_list, env_log_level, env_str, parse_log_level
from smello.config import SmelloConfig
from smello.patches import apply_all as _apply_all
from smello.transport import flush, shutdown
from smello.transport import start_worker as _start_worker

logger = logging.getLogger("smello")
logger.addHandler(logging.NullHandler())

__all__ = ["init", "flush", "shutdown"]
__version__ = "0.14.0"

DEFAULT_REDACT_HEADERS = ["authorization", "x-api-key"]

_config: SmelloConfig | None = None
_patched: bool = False
_atexit_registered: bool = False


def _load_cli_provenance() -> dict[str, str | None]:
    """Read and consume ``_SMELLO_CLI_PROVENANCE`` set by ``smello run``.

    The env var is removed after reading so it does not leak to
    grandchild processes that call ``init()`` independently.
    """
    raw = os.environ.pop("_SMELLO_CLI_PROVENANCE", None)
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}


def _env_provenance(env_var_name: str, cli_prov: dict[str, str | None]) -> str:
    """Return the provenance label for a value resolved from an env var.

    If the CLI set this var, return the flag name (e.g. ``"--debug"``)
    or ``"default"`` for CLI-injected defaults.  Otherwise return the
    env var name (e.g. ``"SMELLO_URL"``).
    """
    if env_var_name in cli_prov:
        flag = cli_prov[env_var_name]
        return flag if flag is not None else "default"
    return env_var_name


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
    app: str | None = None,
    session: str | None = None,
    debug: bool | None = None,
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
    debug                 ``SMELLO_DEBUG``                ``False``
    capture_all           ``SMELLO_CAPTURE_ALL``          ``True``
    capture_hosts         ``SMELLO_CAPTURE_HOSTS``        ``[]``
    ignore_hosts          ``SMELLO_IGNORE_HOSTS``         ``[]``
    redact_headers        ``SMELLO_REDACT_HEADERS``       ``["authorization", "x-api-key"]``
    redact_query_params   ``SMELLO_REDACT_QUERY_PARAMS``  ``[]``
    capture_exceptions    ``SMELLO_CAPTURE_EXCEPTIONS``   ``True``
    capture_logs          ``SMELLO_CAPTURE_LOGS``         ``False``
    log_level             ``SMELLO_LOG_LEVEL``            ``30`` (WARNING)
    ignore_loggers        ``SMELLO_IGNORE_LOGGERS``       ``[]``
    app                   ``SMELLO_APP``                  ``""``
    session               ``SMELLO_SESSION``              ``""``
    ====================  ==============================  ==========================

    When ``debug`` is enabled, Smello logs its resolved configuration,
    library patching, capture decisions, and transport activity to stderr
    via the ``"smello"`` Python logger.  You can also configure this logger
    manually (e.g. ``logging.getLogger("smello").setLevel(logging.DEBUG)``)
    without setting the ``debug`` flag.

    ``app`` tags every captured event with an application name, useful when
    multiple services share a single Smello server. ``session`` tags events
    with a debugging session identifier so you can isolate a specific run.

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

    provenance: dict[str, str] = {}
    cli_prov = _load_cli_provenance()

    # Resolve debug first so logging is active for subsequent resolution.
    if debug is not None:
        provenance["debug"] = "param"
    else:
        env_val = env_bool("DEBUG")
        if env_val is not None:
            debug = env_val
            provenance["debug"] = _env_provenance("SMELLO_DEBUG", cli_prov)
        else:
            debug = False
            provenance["debug"] = "default"

    if debug:
        setup_debug_logging()
    elif _config is not None and _config.debug:
        teardown_debug_logging()

    # Resolve: explicit param > env var
    if server_url is not None:
        provenance["server_url"] = "param"
    else:
        server_url = env_str("URL")
        if server_url:
            provenance["server_url"] = _env_provenance("SMELLO_URL", cli_prov)
        else:
            provenance["server_url"] = "default"
    if not server_url:
        logger.warning(
            "smello.init() called without a server URL. "
            "Set SMELLO_URL or pass server_url= to activate. Doing nothing."
        )
        return

    if capture_all is not None:
        provenance["capture_all"] = "param"
    else:
        env_val = env_bool("CAPTURE_ALL")
        if env_val is not None:
            capture_all = env_val
            provenance["capture_all"] = _env_provenance("SMELLO_CAPTURE_ALL", cli_prov)
        else:
            capture_all = True
            provenance["capture_all"] = "default"

    if capture_hosts is not None:
        provenance["capture_hosts"] = "param"
    else:
        env_val = env_list("CAPTURE_HOSTS")
        capture_hosts = env_val or []
        provenance["capture_hosts"] = (
            _env_provenance("SMELLO_CAPTURE_HOSTS", cli_prov) if env_val else "default"
        )

    if ignore_hosts is not None:
        provenance["ignore_hosts"] = "param"
    else:
        env_val = env_list("IGNORE_HOSTS")
        ignore_hosts = env_val or []
        provenance["ignore_hosts"] = (
            _env_provenance("SMELLO_IGNORE_HOSTS", cli_prov) if env_val else "default"
        )

    if redact_headers is not None:
        provenance["redact_headers"] = "param"
    else:
        env_headers = env_list("REDACT_HEADERS")
        redact_headers = (
            env_headers if env_headers is not None else list(DEFAULT_REDACT_HEADERS)
        )
        provenance["redact_headers"] = (
            _env_provenance("SMELLO_REDACT_HEADERS", cli_prov)
            if env_headers is not None
            else "default"
        )

    if redact_query_params is not None:
        provenance["redact_query_params"] = "param"
    else:
        env_val = env_list("REDACT_QUERY_PARAMS")
        redact_query_params = env_val or []
        provenance["redact_query_params"] = (
            _env_provenance("SMELLO_REDACT_QUERY_PARAMS", cli_prov)
            if env_val
            else "default"
        )

    if capture_exceptions is not None:
        provenance["capture_exceptions"] = "param"
    else:
        env_val = env_bool("CAPTURE_EXCEPTIONS")
        if env_val is not None:
            capture_exceptions = env_val
            provenance["capture_exceptions"] = _env_provenance(
                "SMELLO_CAPTURE_EXCEPTIONS", cli_prov
            )
        else:
            capture_exceptions = True
            provenance["capture_exceptions"] = "default"

    if capture_logs is not None:
        provenance["capture_logs"] = "param"
    else:
        env_val = env_bool("CAPTURE_LOGS")
        if env_val is not None:
            capture_logs = env_val
            provenance["capture_logs"] = _env_provenance(
                "SMELLO_CAPTURE_LOGS", cli_prov
            )
        else:
            capture_logs = False
            provenance["capture_logs"] = "default"

    if ignore_loggers is not None:
        provenance["ignore_loggers"] = "param"
    else:
        env_val = env_list("IGNORE_LOGGERS")
        ignore_loggers = env_val or []
        provenance["ignore_loggers"] = (
            _env_provenance("SMELLO_IGNORE_LOGGERS", cli_prov) if env_val else "default"
        )

    if log_level is not None:
        provenance["log_level"] = "param"
        if isinstance(log_level, str):
            parsed = parse_log_level(log_level)
            if parsed is None:
                logger.warning(
                    "Unrecognised log_level %r, falling back to WARNING", log_level
                )
                log_level = logging.WARNING
            else:
                log_level = parsed
    else:
        env_val = env_log_level("LOG_LEVEL")
        if env_val is not None:
            log_level = env_val
            provenance["log_level"] = _env_provenance("SMELLO_LOG_LEVEL", cli_prov)
        else:
            log_level = logging.WARNING
            provenance["log_level"] = "default"

    if app is not None:
        provenance["app"] = "param"
    else:
        env_val = env_str("APP")
        app = env_val or ""
        provenance["app"] = (
            _env_provenance("SMELLO_APP", cli_prov) if env_val else "default"
        )

    if session is not None:
        provenance["session"] = "param"
    else:
        env_val = env_str("SESSION")
        session = env_val or ""
        provenance["session"] = (
            _env_provenance("SMELLO_SESSION", cli_prov) if env_val else "default"
        )

    resolved_url = server_url.rstrip("/")
    normalized_redact_headers = [h.lower() for h in redact_headers]
    normalized_redact_query_params = [p.lower() for p in redact_query_params]

    log_resolved_config(
        provenance,
        server_url=resolved_url,
        debug=debug,
        capture_all=capture_all,
        capture_hosts=capture_hosts,
        ignore_hosts=ignore_hosts,
        redact_headers=redact_headers,
        redact_query_params=redact_query_params,
        capture_exceptions=capture_exceptions,
        capture_logs=capture_logs,
        log_level=log_level,
        ignore_loggers=ignore_loggers,
        app=app,
        session=session,
    )

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
            app=app,
            session=session,
            debug=debug,
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
        _config.app = app
        _config.session = session
        _config.debug = debug

    # Always ignore the smello server itself
    server_host = urlparse(_config.server_url).hostname
    if server_host and server_host not in _config.ignore_hosts:
        _config.ignore_hosts.append(server_host)

    # Start transport worker (idempotent — start_worker guards against re-start)
    _start_worker(_config.server_url, app=_config.app, session=_config.session)

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

    if _config.debug:
        check_connectivity(_config.server_url)
