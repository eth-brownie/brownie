#!/usr/bin/python3

from typing import Final

from packaging.version import Version as PackagingVersion
from semantic_version import Version

from . import hex
from ._color import Color, notify

color: Final = Color()
bytes_to_hexstring: Final = hex.bytes_to_hexstring
hexbytes_to_hexstring: Final = hex.hexbytes_to_hexstring

__all__ = ["Color", "color", "notify", "bytes_to_hexstring", "hexbytes_to_hexstring"]


def _to_vyper_semver(version: PackagingVersion) -> Version:
    """Use Vyper's release identifiers for both pragmas and compiler selection."""
    prerelease: tuple[str, ...] = ()
    if version.pre is not None:
        phase, number = version.pre
        prerelease = ({"a": "alpha", "b": "beta", "rc": "rc"}[phase], str(number))
    return Version(
        major=version.major,
        minor=version.minor,
        patch=version.micro,
        prerelease=prerelease,
    )
