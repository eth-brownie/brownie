#!/usr/bin/python3

import json

import pytest

from brownie.exceptions import InvalidManifest
from brownie.project.ethpm import verify_manifest


def pin(ipfs, manifest):
    ipfs._assets["invalid"] = json.dumps(manifest, sort_keys=True, separators=(",", ":"))


def test_not_json(ipfs_mock):
    ipfs_mock._assets["invalid"] = "foo"
    with pytest.raises(InvalidManifest, match="URI did not return valid JSON encoded data"):
        verify_manifest("invalid", "1.0.0", "invalid")


def test_packing(ipfs_mock):
    ipfs_mock._assets["invalid"] = '{"version": "1.0.0"}'
    with pytest.raises(InvalidManifest, match="JSON data is not tightly packed with sorted keys"):
        verify_manifest("invalid", "1.0.0", "invalid")


def test_invalid_package_name(ipfs_mock):
    manifest = {"manifest_version": "2", "package_name": "Not a good name!", "version": "1.0.0"}
    pin(ipfs_mock, manifest)
    with pytest.raises(ValueError):
        verify_manifest("Not a good name!", "1.0.0", "invalid")


def test_fields(ipfs_mock):
    manifest = {"manifest_version": "2", "package_name": "invalid", "version": "1.0.0"}
    for key, value in manifest.items():
        manifest[key] += "xx"
        pin(ipfs_mock, manifest)
        with pytest.raises(InvalidManifest, match=f"Missing or invalid field: {key}"):
            verify_manifest("invalid", "1.0.0", "invalid")
        del manifest[key]
        pin(ipfs_mock, manifest)
        with pytest.raises(InvalidManifest, match=f"Missing or invalid field: {key}"):
            verify_manifest("invalid", "1.0.0", "invalid")
        manifest[key] = value
        pin(ipfs_mock, manifest)
        verify_manifest("invalid", "1.0.0", "invalid")


def test_cannot_process(ipfs_mock):
    manifest = {
        "manifest_version": "2",
        "package_name": "invalid",
        "version": "1.0.0",
        "sources": "foo",
    }
    pin(ipfs_mock, manifest)
    with pytest.raises(InvalidManifest, match="Cannot process manifest"):
        verify_manifest("invalid", "1.0.0", "invalid")
