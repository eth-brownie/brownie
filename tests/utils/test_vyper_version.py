import pytest
from packaging.version import Version as PackagingVersion
from semantic_version import Version

from brownie.utils import _to_vyper_semver


@pytest.mark.parametrize(
    "release, expected",
    [
        ("0.1.0b16", "0.1.0-beta.16"),
        ("0.1.0Beta17", "0.1.0-beta.17"),
        ("0.4.0a2", "0.4.0-alpha.2"),
        ("0.4.0rc1", "0.4.0-rc.1"),
        ("0.4.3", "0.4.3"),
    ],
)
def test_vyper_release_identifiers(release, expected):
    assert _to_vyper_semver(PackagingVersion(release)) == Version(expected)
