"""Auto-init Smello when this directory is on PYTHONPATH.

Python's ``site`` module imports a top-level ``sitecustomize`` module at
interpreter startup, before any user code runs. ``smello run`` prepends the
directory containing this file to ``PYTHONPATH``, which makes ``import
sitecustomize`` resolve here. Subprocess instrumentation propagates
naturally because PYTHONPATH is inherited.

The bootstrap is defensive: if anything fails (smello not importable, no
server URL configured, install error) it stays out of the way rather than
crashing the wrapped program.

We intentionally do not chain-load any pre-existing user ``sitecustomize``
on ``sys.path``. Doing so safely requires fiddling with ``sys.modules``
mid-import, which is fragile. Users with a custom sitecustomize should
call ``smello.init()`` directly from it instead of using ``smello run``.
"""

from __future__ import annotations

import os


def _activate() -> None:
    if not os.environ.get("SMELLO_URL"):
        return
    try:
        import smello  # noqa: PLC0415

        smello.init()
    except Exception:
        pass


_activate()
