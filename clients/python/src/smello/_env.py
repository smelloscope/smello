"""Read SMELLO_* environment variables."""

from __future__ import annotations

import logging
import os

TRUTHY = frozenset({"true", "1", "yes"})
FALSY = frozenset({"false", "0", "no"})


def env_str(name: str) -> str | None:
    """Read ``SMELLO_{name}`` from the environment.

    Returns the stripped value, or ``None`` if unset or empty.
    """
    value = os.environ.get(f"SMELLO_{name}", "").strip()
    return value if value else None


def env_bool(name: str) -> bool | None:
    """Read ``SMELLO_{name}`` as a boolean.

    Truthy: ``true``, ``1``, ``yes`` (case-insensitive).
    Falsy:  ``false``, ``0``, ``no`` (case-insensitive).
    Returns ``None`` if unset, empty, or unrecognised.
    """
    raw = env_str(name)
    if raw is None:
        return None
    lowered = raw.lower()
    if lowered in TRUTHY:
        return True
    if lowered in FALSY:
        return False
    return None


def env_int(name: str) -> int | None:
    """Read ``SMELLO_{name}`` as an integer.

    Returns ``None`` if unset, empty, or not a valid integer.
    """
    raw = env_str(name)
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def env_log_level(name: str) -> int | None:
    """Read ``SMELLO_{name}`` as a log level (int or name like ``DEBUG``).

    Returns ``None`` if unset, empty, or unrecognised.
    """
    raw = env_str(name)
    if raw is None:
        return None
    return parse_log_level(raw)


def parse_log_level(value: str) -> int | None:
    """Parse a log level string that is either numeric or a level name.

    Accepts ``"10"``, ``"DEBUG"``, ``"debug"``, etc.
    Returns ``None`` for unrecognised values.
    """
    try:
        return int(value)
    except ValueError:
        pass
    level = logging.getLevelNamesMapping().get(value.upper())
    return level


def env_list(name: str) -> list[str] | None:
    """Read ``SMELLO_{name}`` as a comma-separated list.

    Returns a list of stripped, non-empty items, or ``None`` if the
    variable is unset or empty.
    """
    raw = env_str(name)
    if raw is None:
        return None
    items = [item.strip() for item in raw.split(",") if item.strip()]
    return items if items else None
