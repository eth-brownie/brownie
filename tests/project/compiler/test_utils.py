#!/usr/bin/python3

from packaging.version import Version

from brownie.project.compiler.utils import parse_compiler_version, parse_compiler_versions


def test_parse_compiler_version_preserves_packaging_version():
    version = Version("0.4.25")

    assert parse_compiler_version(version) == version


def test_parse_compiler_version_ignores_solidity_build_metadata():
    version = parse_compiler_version(Version("0.5.17+commit.d19bba13"))

    assert version == Version("0.5.17")


def test_parse_compiler_version_normalizes_pep440_prerelease():
    assert parse_compiler_version(Version("0.1.0b16")) == Version("0.1.0b16")


def test_parse_compiler_versions_converts_lists():
    versions = parse_compiler_versions([Version("0.1.0b16"), Version("0.2.0")])

    assert versions == [Version("0.1.0b16"), Version("0.2.0")]
