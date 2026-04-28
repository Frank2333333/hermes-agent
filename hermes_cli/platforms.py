"""
Shared platform registry for the enterprise build.

Only the CLI and API server remain as supported platform surfaces. Import
``PLATFORMS`` from here instead of duplicating platform metadata elsewhere.
"""

from collections import OrderedDict
from typing import NamedTuple


class PlatformInfo(NamedTuple):
    """Metadata for a single platform entry."""

    label: str
    default_toolset: str


PLATFORMS: OrderedDict[str, PlatformInfo] = OrderedDict(
    [
        ("cli", PlatformInfo(label="CLI", default_toolset="hermes-cli")),
        (
            "api_server",
            PlatformInfo(label="API Server", default_toolset="hermes-api-server"),
        ),
    ]
)


def platform_label(key: str, default: str = "") -> str:
    """Return the display label for a platform key, or *default*."""

    info = PLATFORMS.get(key)
    return info.label if info is not None else default
