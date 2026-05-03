"""Monkey-patches for HTTP client libraries and Python runtime hooks."""

from smello.config import SmelloConfig

# Alias imports to avoid shadowing the submodule names (patch_grpc,
# patch_httpx, patch_requests).  unittest.mock on Python < 3.12 resolves
# "smello.patches.patch_grpc.send_http" via getattr, so the module attribute
# must remain the *module*, not the function.
from smello.patches.patch_aiohttp import patch_aiohttp as _patch_aiohttp
from smello.patches.patch_botocore import patch_botocore as _patch_botocore
from smello.patches.patch_excepthook import patch_excepthook as _patch_excepthook
from smello.patches.patch_grpc import patch_grpc as _patch_grpc
from smello.patches.patch_httpx import patch_httpx as _patch_httpx
from smello.patches.patch_logging import patch_logging as _patch_logging
from smello.patches.patch_requests import patch_requests as _patch_requests


def apply_all(config: SmelloConfig) -> None:
    """Apply all available patches."""
    _patch_requests(config)
    _patch_httpx(config)
    _patch_grpc(config)
    _patch_botocore(config)
    _patch_aiohttp(config)
    _patch_excepthook(config)
    _patch_logging(config)
