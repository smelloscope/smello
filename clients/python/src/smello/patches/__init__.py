"""Monkey-patches for HTTP client libraries."""

from smello.config import SmelloConfig

# Alias imports to avoid shadowing the submodule names (patch_grpc,
# patch_httpx, patch_requests).  unittest.mock on Python < 3.12 resolves
# "smello.patches.patch_grpc.send" via getattr, so the module attribute
# must remain the *module*, not the function.
from smello.patches.patch_grpc import patch_grpc as _patch_grpc
from smello.patches.patch_httpx import patch_httpx as _patch_httpx
from smello.patches.patch_requests import patch_requests as _patch_requests


def apply_all(config: SmelloConfig) -> None:
    """Apply all available patches."""
    _patch_requests(config)
    _patch_httpx(config)
    _patch_grpc(config)
