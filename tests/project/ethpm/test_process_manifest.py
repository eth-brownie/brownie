#!/usr/bin/python3

import pytest

from brownie.exceptions import InvalidManifest
from brownie.project import ethpm

TEST_MANIFEST = {"manifest_version": "2", "version": "1.0.0", "package_name": "simple"}


def test_invalid_manifest():
    with pytest.raises(InvalidManifest):
        ethpm.process_manifest({})
    with pytest.raises(InvalidManifest):
        ethpm.process_manifest({"manifest_version": "1"})


def test_source_paths():
    original = TEST_MANIFEST.copy()
    original["sources"] = {"./simple.sol": "ipfs://testipfs-simple-source"}

    processed = ethpm.process_manifest(original)
    assert list(processed["sources"]) == ["contracts/simple.sol"]

    original["sources"] = {"./contracts/simple.sol": "ipfs://testipfs-simple-source"}
    assert processed == ethpm.process_manifest(original)

    original["sources"] = {"simple.sol": "ipfs://testipfs-simple-source"}
    assert processed == ethpm.process_manifest(original)

    original["sources"] = {"contracts/simple.sol": "ipfs://testipfs-simple-source"}
    assert processed == ethpm.process_manifest(original)


def test_source_paths_with_interface():
    original = TEST_MANIFEST.copy()
    original["sources"] = {
        "./contracts/foo.sol": "ipfs://testipfs-simple-source",
        "./interfaces/bar.sol": "ipfs://testipfs-simple-source",
    }

    processed = ethpm.process_manifest(original)
    assert sorted(processed["sources"]) == ["contracts/foo.sol", "interfaces/bar.sol"]

    original["sources"] = {
        "contracts/foo.sol": "ipfs://testipfs-simple-source",
        "interfaces/bar.sol": "ipfs://testipfs-simple-source",
    }
    assert processed == ethpm.process_manifest(original)
