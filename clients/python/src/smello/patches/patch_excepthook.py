"""Capture unhandled exceptions via sys.excepthook and threading.excepthook."""

import linecache
import logging
import sys
import threading
import traceback
import uuid
from datetime import datetime, timezone

from smello import transport
from smello.config import SmelloConfig

logger = logging.getLogger(__name__)

_patched = False

# Number of source lines to capture before/after the failing line.
_CONTEXT_LINES = 5


def _get_frame_source(
    filename: str | None, lineno: int | None, count: int = _CONTEXT_LINES
) -> tuple[list[str], str | None, list[str]]:
    """Return (pre_lines, error_line, post_lines) from the source file.

    All lines retain their original indentation so they line up when rendered
    together. Returns ``([], None, [])`` when the source isn't available — e.g.
    ``<frozen ...>``, ``<string>``, files inside zipped wheels, or generated
    code. Trailing newlines are stripped.
    """
    if not filename or filename.startswith("<") or lineno is None or lineno < 1:
        return [], None, []
    try:
        all_lines = linecache.getlines(filename)
    except Exception:
        return [], None, []
    if not all_lines:
        return [], None, []
    pre_start = max(0, lineno - 1 - count)
    pre = [line.rstrip("\n") for line in all_lines[pre_start : lineno - 1]]
    error_line = (
        all_lines[lineno - 1].rstrip("\n") if 1 <= lineno <= len(all_lines) else None
    )
    post = [line.rstrip("\n") for line in all_lines[lineno : lineno + count]]
    return pre, error_line, post


def patch_excepthook(config: SmelloConfig) -> None:
    """Install exception hooks to capture unhandled exceptions."""
    global _patched
    if _patched:
        return
    if not config.capture_exceptions:
        return
    _patched = True

    original_excepthook = sys.excepthook

    def smello_excepthook(exc_type, exc_value, exc_tb):
        try:
            _capture_exception(exc_type, exc_value, exc_tb)
            transport.flush(timeout=2.0)
        except Exception:
            logger.debug("Failed to capture exception", exc_info=True)
        finally:
            original_excepthook(exc_type, exc_value, exc_tb)

    sys.excepthook = smello_excepthook

    # Python 3.8+ threading exception hook
    if hasattr(sys, "unraisablehook"):
        pass  # unraisable exceptions are edge-case; skip for now

    original_threading_excepthook = threading.excepthook

    def smello_threading_excepthook(args):
        try:
            _capture_exception(args.exc_type, args.exc_value, args.exc_traceback)
        except Exception:
            logger.debug("Failed to capture thread exception", exc_info=True)
        finally:
            original_threading_excepthook(args)

    threading.excepthook = smello_threading_excepthook


def _capture_exception(exc_type, exc_value, exc_tb):
    """Serialize and send an exception event."""
    if exc_type is None or exc_value is None:
        return

    frames = []
    if exc_tb is not None:
        for frame_info in traceback.extract_tb(exc_tb):
            pre_context, error_line, post_context = _get_frame_source(
                frame_info.filename, frame_info.lineno
            )
            # Prefer linecache's unstripped error line so it lines up with the
            # surrounding context. Fall back to traceback's stripped line when
            # the source isn't available (synthetic filenames, zipped wheels…).
            context_line = error_line if error_line is not None else frame_info.line
            frames.append(
                {
                    "filename": frame_info.filename,
                    "lineno": frame_info.lineno,
                    "function": frame_info.name,
                    "context_line": context_line,
                    "pre_context": pre_context,
                    "post_context": post_context,
                }
            )

    tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))

    data = {
        "exc_type": exc_type.__name__,
        "exc_value": str(exc_value),
        "exc_module": getattr(exc_type, "__module__", None),
        "traceback_text": tb_text,
        "frames": frames,
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    transport.send_event("exception", data)
