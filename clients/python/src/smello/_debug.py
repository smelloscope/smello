"""Debug logging helpers for the Smello client SDK."""

import logging
import sys
import urllib.request

_HANDLER_ATTR = "_smello_debug_handler"


def setup_debug_logging() -> None:
    """Attach a stderr handler to the ``"smello"`` logger at DEBUG level.

    Idempotent — safe to call multiple times.  Only touches the handler
    it owns (tagged with ``_smello_debug_handler``), so it never
    interferes with handlers the user attached manually.
    """
    smello_logger = logging.getLogger("smello")
    smello_logger.setLevel(logging.DEBUG)
    smello_logger.propagate = False

    for h in smello_logger.handlers:
        if getattr(h, _HANDLER_ATTR, False):
            return

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("smello: %(message)s"))
    setattr(handler, _HANDLER_ATTR, True)
    smello_logger.addHandler(handler)


def teardown_debug_logging() -> None:
    """Remove the handler installed by :func:`setup_debug_logging`.

    Only removes Smello's own handler; user-attached handlers and the
    logger level are left untouched.
    """
    smello_logger = logging.getLogger("smello")
    smello_logger.handlers = [
        h for h in smello_logger.handlers if not getattr(h, _HANDLER_ATTR, False)
    ]


def check_connectivity(server_url: str) -> None:
    """Ping the Smello server and log the result. Never raises."""
    logger = logging.getLogger("smello")
    try:
        req = urllib.request.Request(f"{server_url}/api/meta", method="GET")
        resp = urllib.request.urlopen(req, timeout=2)  # noqa: S310
        logger.debug("connected to %s (%d)", server_url, resp.status)
    except Exception as err:
        logger.warning("failed to reach %s (%s)", server_url, err)


def log_resolved_config(provenance: dict[str, str], **fields: object) -> None:
    """Log the resolved configuration with provenance info."""
    logger = logging.getLogger("smello")
    lines = []
    for name, value in fields.items():
        source = provenance.get(name, "default")
        lines.append(f"  {name} = {value} ({source})")
    logger.debug("resolved config:\n%s", "\n".join(lines))
