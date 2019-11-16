#!/usr/bin/python3

import json

import pytest

from brownie.project import ethpm

ETHPM_CONFIG = {
    "package_name": "testpackage",
    "version": "1.0.0",
    "settings": {"deployment_networks": False, "include_dependencies": False},
}
ROPSTEN_GENESIS_HASH = "41941023680923e0fe4d74a34bdac8141f2540e3ae90623718e47d66d1ca4a2d"
MAINNET_GENESIS_HASH = "d4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3"


def test_standard_fields(tp_path):
    manifest = ethpm.create_manifest(tp_path, ETHPM_CONFIG, False)
    assert manifest["manifest_version"] == "2"
    assert manifest["package_name"] == "testpackage"
    assert manifest["version"] == "1.0.0"
    assert manifest["sources"]
    assert manifest["contract_types"]


def test_meta(tp_path):
    package_config = ETHPM_CONFIG.copy()
    package_config["meta"] = {
        "description": "blahblahblah",
        "authors": ["foo", None],
        "keywords": [None, None],
        "license": None,
        "links": {"website": "www.potato.com", "documentation": None},
        "foo": "bar",
    }
    manifest = ethpm.create_manifest(tp_path, package_config, False)
    assert manifest["meta"] == {
        "description": "blahblahblah",
        "authors": ["foo"],
        "links": {"website": "www.potato.com"},
        "foo": "bar",
    }


def test_missing_fields(tp_path):
    for key in ETHPM_CONFIG:
        package_config = ETHPM_CONFIG.copy()
        del package_config[key]
        with pytest.raises(KeyError):
            ethpm.create_manifest(tp_path, package_config, False)


def test_field_as_none(tp_path):
    for key in ETHPM_CONFIG:
        package_config = ETHPM_CONFIG.copy()
        package_config[key] = None
        with pytest.raises(KeyError):
            ethpm.create_manifest(tp_path, package_config, False)


def test_sources(tp_path):
    manifest = ethpm.create_manifest(tp_path, ETHPM_CONFIG, False)
    assert sorted(manifest["sources"]) == [
        "./BrownieTester.sol",
        "./EVMTester.sol",
        "./SafeMath.sol",
        "./Unimplemented.sol",
    ]


def test_contract_types(tp_path):
    manifest = ethpm.create_manifest(tp_path, ETHPM_CONFIG, False)
    with tp_path.joinpath("build/contracts/EVMTester.json").open() as fp:
        build = json.load(fp)
    assert "EVMTester" in manifest["contract_types"]
    assert manifest["contract_types"]["EVMTester"] == {
        "contract_name": "EVMTester",
        "source_path": f"./EVMTester.sol",
        "deployment_bytecode": {"bytecode": f"0x{build['bytecode']}"},
        "runtime_bytecode": {"bytecode": f"0x{build['deployedBytecode']}"},
        "abi": build["abi"],
        "compiler": {
            "name": "solc",
            "version": build["compiler"]["version"],
            "settings": {
                "optimizer": {
                    "enabled": build["compiler"]["optimize"],
                    "runs": build["compiler"]["runs"],
                },
                "evmVersion": build["compiler"]["evm_version"],
            },
        },
    }


def test_deployments(testproject, network, web3):
    BrownieTester = testproject.BrownieTester

    network.connect("mainnet")
    BrownieTester.at("0xdAC17F958D2ee523a2206206994597C13D831ec7")
    BrownieTester.at("0xB8c77482e45F1F44dE1745F52C74426C631bDD52")
    mainnet_uri = web3.chain_uri
    network.disconnect(False)

    network.connect("ropsten")
    BrownieTester.at("0xBcd0a9167015Ee213Ba01dAff79d60CD221B0cAC")
    ropsten_uri = web3.chain_uri
    network.disconnect(False)

    expected = {
        ropsten_uri: {
            "BrownieTester": {
                "address": "0xBcd0a9167015Ee213Ba01dAff79d60CD221B0cAC",
                "contract_type": "BrownieTester",
            }
        },
        mainnet_uri: {
            "BrownieTester": {
                "address": "0xB8c77482e45F1F44dE1745F52C74426C631bDD52",
                "contract_type": "BrownieTester",
            },
            "BrownieTester-1": {
                "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                "contract_type": "BrownieTester",
            },
        },
    }

    package_config = ETHPM_CONFIG.copy()

    package_config["settings"]["deployment_networks"] = "*"
    manifest = ethpm.create_manifest(testproject._path, package_config, False)
    assert manifest["deployments"] == expected

    package_config["settings"]["deployment_networks"] = ["*"]
    assert ethpm.create_manifest(testproject._path, package_config, False) == manifest

    package_config["settings"]["deployment_networks"] = "ropsten"
    manifest = ethpm.create_manifest(testproject._path, package_config, False)
    assert manifest["deployments"] == {ropsten_uri: expected[ropsten_uri]}

    package_config["settings"]["deployment_networks"] = ["mainnet"]
    manifest = ethpm.create_manifest(testproject._path, package_config, False)
    assert manifest["deployments"] == {mainnet_uri: expected[mainnet_uri]}

    package_config["settings"]["deployment_networks"] = ["potatonet"]
    manifest = ethpm.create_manifest(testproject._path, package_config, False)
    assert "deployments" not in manifest


def test_dependencies(tp_path):
    pass
