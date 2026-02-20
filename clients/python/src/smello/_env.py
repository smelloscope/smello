"""Read SMELLO_* environment variables."""

from __future__ import annotations

import os

_TRUTHY = frozenset({"true", "1", "yes"})
_FALSY = frozenset({"false", "0", "no"})


def _env_str(name: str) -> str | None:
    """Read ``SMELLO_{name}`` from the environment.

    Returns the stripped value, or ``None`` if unset or empty.
    """
    value = os.environ.get(f"SMELLO_{name}", "").strip()
    return value if value else None


def _env_bool(name: str) -> bool | None:
    """Read ``SMELLO_{name}`` as a boolean.

    Truthy: ``true``, ``1``, ``yes`` (case-insensitive).
    Falsy:  ``false``, ``0``, ``no`` (case-insensitive).
    Returns ``None`` if unset, empty, or unrecognised.
    """
    raw = _env_str(name)
    if raw is None:
        return None
    lowered = raw.lower()
    if lowered in _TRUTHY:
        return True
    if lowered in _FALSY:
        return False
    return None


def _env_list(name: str) -> list[str] | None:
    """Read ``SMELLO_{name}`` as a comma-separated list.

    Returns a list of stripped, non-empty items, or ``None`` if the
    variable is unset or empty.
    """
    raw = _env_str(name)
    if raw is None:
        return None
    items = [item.strip() for item in raw.split(",") if item.strip()]
    return items if items else None
