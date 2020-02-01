#!/usr/bin/python3

import json

import pytest

from brownie.exceptions import InvalidManifest
from brownie.project import ethpm

ETHPM_CONFIG = {
    "package_name": "testpackage",
    "version": "1.0.0",
    "settings": {"deployment_networks": False, "include_dependencies": False},
}

DEPLOYMENTS_ROPSTEN = {
    "BrownieTester": {
        "address": "0xBcd0a9167015Ee213Ba01dAff79d60CD221B0cAC",
        "contract_type": "BrownieTester",
    }
}
DEPLOYMENTS_MAINNET = {
    "BrownieTester": {
        "address": "0xB8c77482e45F1F44dE1745F52C74426C631bDD52",
        "contract_type": "BrownieTester",
    },
    "BrownieTester-1": {
        "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "contract_type": "BrownieTester",
    },
}


def test_standard_fields(tp_path):
    manifest, _ = ethpm.create_manifest(tp_path, ETHPM_CONFIG)
    assert manifest["manifest_version"] == "2"
    assert manifest["package_name"] == "testpackage"
    assert manifest["version"] == "1.0.0"
    assert manifest["sources"]
    assert manifest["contract_types"]
    assert "build_dependencies" not in manifest


def test_meta(np_path):
    package_config = ETHPM_CONFIG.copy()
    package_config["meta"] = {
        "description": "blahblahblah",
        "authors": ["foo", None],
        "keywords": [None, None],
        "license": None,
        "links": {"website": "www.potato.com", "documentation": None},
        "foo": "bar",
    }
    manifest, _ = ethpm.create_manifest(np_path, package_config)
    assert manifest["meta"] == {
        "description": "blahblahblah",
        "authors": ["foo"],
        "links": {"website": "www.potato.com"},
        "foo": "bar",
    }


def test_invalid_package_name(np_path):
    package_config = ETHPM_CONFIG.copy()
    package_config["package_name"] = "A Very Invalid Name!"
    with pytest.raises(ValueError):
        ethpm.create_manifest(np_path, package_config)


def test_missing_fields(np_path):
    for key in ETHPM_CONFIG:
        package_config = ETHPM_CONFIG.copy()
        del package_config[key]
        with pytest.raises(KeyError):
            ethpm.create_manifest(np_path, package_config)


def test_field_as_none(np_path):
    for key in ETHPM_CONFIG:
        package_config = ETHPM_CONFIG.copy()
        package_config[key] = None
        with pytest.raises(KeyError):
            ethpm.create_manifest(np_path, package_config)


def test_base_path(newproject, solc5source):
    with newproject._path.joinpath("contracts/Foo.sol").open("w") as fp:
        fp.write(solc5source)
    newproject.load()
    manifest, _ = ethpm.create_manifest(newproject._path, ETHPM_CONFIG)
    assert sorted(manifest["sources"]) == ["./Foo.sol"]
    newproject.close()

    # adding an interface should change the base path
    with newproject._path.joinpath("interfaces/Baz.sol").open("w") as fp:
        fp.write("pragma solidity ^0.5.0; interface Baz {}")
    newproject.load()
    manifest, _ = ethpm.create_manifest(newproject._path, ETHPM_CONFIG)
    assert sorted(manifest["sources"]) == ["./contracts/Foo.sol", "./interfaces/Baz.sol"]


def test_sources(tp_path):
    manifest, _ = ethpm.create_manifest(tp_path, ETHPM_CONFIG)
    assert sorted(manifest["sources"]) == [
        "./BrownieTester.sol",
        "./EVMTester.sol",
        "./PackageRegistry.sol",
        "./SafeMath.sol",
        "./VyperTester.vy",
    ]


def test_contract_types(tp_path):
    manifest, _ = ethpm.create_manifest(tp_path, ETHPM_CONFIG)
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


def test_contract_types_unimplemented(newproject):
    code = """
pragma solidity ^0.5.0;
contract A { function bar() external returns (bool); }
interface B { function bar() external returns (bool); }
contract C { function bar() external returns (bool) { return true; } }
"""

    with newproject._path.joinpath("contracts/Foo.sol").open("w") as fp:
        fp.write(code)
    newproject.load()
    manifest, _ = ethpm.create_manifest(newproject._path, ETHPM_CONFIG)

    # base contracts are not included
    assert "A" not in manifest["contract_types"]
    # interfaces are included
    assert "B" in manifest["contract_types"]
    # compilable contracts are included
    assert "C" in manifest["contract_types"]


def test_contract_types_json_interface(np_path):
    with np_path.joinpath("interfaces/Bar.json").open("w") as fp:
        json.dump([{"inputs": [], "name": "baz", "outputs": []}], fp)
    manifest, _ = ethpm.create_manifest(np_path, ETHPM_CONFIG)
    assert "Bar" in manifest["contract_types"]


def test_dependencies_include(dep_project):
    package_config = ETHPM_CONFIG.copy()
    package_config["settings"]["include_dependencies"] = True
    manifest, _ = ethpm.create_manifest(dep_project._path, package_config)
    assert "build_dependencies" not in manifest
    assert "./math/Math.sol" in manifest["sources"]
    assert "Math" in manifest["contract_types"]
    assert "./utils/Arrays.sol" in manifest["sources"]
    assert "Arrays" in manifest["contract_types"]
    assert "deployments" not in manifest


def test_dependencies_not_include(dep_project):
    package_config = ETHPM_CONFIG.copy()
    package_config["settings"]["include_dependencies"] = False
    manifest, _ = ethpm.create_manifest(dep_project._path, package_config)
    assert manifest["build_dependencies"] == {"utils": "ipfs://testipfs-utils"}
    assert "./math/Math.sol" not in manifest["sources"]
    assert "Math" not in manifest["contract_types"]
    assert "./utils/Arrays.sol" not in manifest["sources"]
    assert "Arrays" not in manifest["contract_types"]
    assert "deployments" not in manifest


def test_dependencies_modified_source(dep_project):
    package_config = ETHPM_CONFIG.copy()
    package_config["settings"]["include_dependencies"] = False
    with dep_project._path.joinpath("contracts/math/Math.sol").open("a") as fp:
        fp.write("\n")
    with pytest.raises(InvalidManifest):
        ethpm.create_manifest(dep_project._path, package_config)


def test_deployments_ropsten(tp_path, deployments, ropsten_uri):
    package_config = ETHPM_CONFIG.copy()
    package_config["settings"]["deployment_networks"] = "ropsten"

    manifest, _ = ethpm.create_manifest(tp_path, package_config)
    assert manifest["deployments"] == {ropsten_uri: DEPLOYMENTS_ROPSTEN}


def test_deployments_mainnet(tp_path, deployments, mainnet_uri):
    package_config = ETHPM_CONFIG.copy()
    package_config["settings"]["deployment_networks"] = ["mainnet"]

    manifest, _ = ethpm.create_manifest(tp_path, package_config)
    assert manifest["deployments"] == {mainnet_uri: DEPLOYMENTS_MAINNET}


def test_deployments_all(tp_path, deployments, mainnet_uri, ropsten_uri):
    package_config = ETHPM_CONFIG.copy()
    package_config["settings"]["deployment_networks"] = "*"

    manifest, uri = ethpm.create_manifest(tp_path, package_config)
    assert manifest["deployments"] == {
        mainnet_uri: DEPLOYMENTS_MAINNET,
        ropsten_uri: DEPLOYMENTS_ROPSTEN,
    }

    package_config["settings"]["deployment_networks"] = ["mainnet", "ropsten"]
    assert manifest["deployments"], uri == ethpm.create_manifest(tp_path, package_config)


def test_deployments_unknown_network(tp_path, deployments):
    package_config = ETHPM_CONFIG.copy()
    package_config["settings"]["deployment_networks"] = ["potatonet"]

    manifest, _ = ethpm.create_manifest(tp_path, package_config)
    assert "deployments" not in manifest


def test_deployments_changed_source(tp_path, deployments, mainnet_uri):
    address = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
    path = tp_path.joinpath(f"build/deployments/mainnet/{address}.json")
    with path.open() as fp:
        build_json = json.load(fp)
    build_json["bytecode"] += "ff"
    with path.open("w") as fp:
        json.dump(build_json, fp)

    package_config = ETHPM_CONFIG.copy()
    package_config["settings"]["deployment_networks"] = ["mainnet"]

    manifest, _ = ethpm.create_manifest(tp_path, package_config)
    assert manifest["deployments"][mainnet_uri]
    assert address not in [i["address"] for i in manifest["deployments"][mainnet_uri].values()]


def test_deployments_of_dependencies(dep_project, config, accounts):
    config["active_network"]["persist"] = True
    address = dep_project.Math.deploy({"from": accounts[0]}).address

    package_config = ETHPM_CONFIG.copy()
    package_config["settings"]["include_dependencies"] = False
    package_config["settings"]["deployment_networks"] = ["development"]

    manifest, uri = ethpm.create_manifest(dep_project._path, package_config)

    assert "./math/Math.sol" not in manifest["sources"]
    assert "Math" not in manifest["contract_types"]

    assert "utils:Math" in list(manifest["contract_types"])
    assert len(manifest["deployments"]) == 1
    assert list(manifest["deployments"].values())[0] == {
        "Math": {"address": address, "contract_type": "utils:Math"}
    }
    assert manifest["build_dependencies"] == {"utils": "ipfs://testipfs-utils"}


def test_pin_and_get(dep_project):
    package_config = ETHPM_CONFIG.copy()
    package_config["settings"]["include_dependencies"] = False
    manifest, uri = ethpm.create_manifest(dep_project._path, package_config, True)

    process = ethpm.process_manifest(manifest, uri)
    get = ethpm.get_manifest(uri)

    for key in list(process) + list(get):
        if type(process[key]) is str:
            assert process[key] == get[key]
            continue
        for k in list(process[key]) + list(get[key]):
            assert process[key][k] == get[key][k]
