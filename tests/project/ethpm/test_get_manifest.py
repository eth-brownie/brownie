#!/usr/bin/python3

import shutil
from pathlib import Path

from brownie.project import ethpm

ROPSTEN_GENESIS_HASH = "41941023680923e0fe4d74a34bdac8141f2540e3ae90623718e47d66d1ca4a2d"
MAINNET_GENESIS_HASH = "d4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3"


def test_get_manifest_from_ipfs():
    path = Path("brownie/data/ethpm/zeppelin.snakecharmers.eth")
    if path.exists():
        shutil.rmtree(path)
    ethpm.get_manifest("erc1319://zeppelin.snakecharmers.eth:1/access@1.0.0")
    assert Path("brownie/data/ethpm/zeppelin.snakecharmers.eth").exists()
    ethpm.get_manifest("erc1319://zeppelin.snakecharmers.eth:1/access@1.0.0")
    assert Path("brownie/data/ethpm/zeppelin.snakecharmers.eth").exists()


def test_meta_brownie():
    manifest = ethpm.get_manifest("erc1319://zeppelin.snakecharmers.eth:1/access@1.0.0")
    assert manifest["meta_brownie"] == {
        "registry_address": "zeppelin.snakecharmers.eth",
        "manifest_uri": "ipfs://QmWqn5uYx9LvV4aqj2qZ5FiFZykmS3LGdLpod7XLjxPVYr",
    }


def test_get_mock_manifests():
    ethpm.get_manifest("ipfs://testipfs-math")
    ethpm.get_manifest("ipfs://testipfs-utils")
    ethpm.get_manifest("ipfs://testipfs-complex")


def test_dependency_paths():
    sources = ethpm.get_manifest("ipfs://testipfs-complex")["sources"]
    assert "contracts/Complex.sol" in sources
    assert "contracts/math/SafeMath.sol" in sources
    assert "contracts/utils/Arrays.sol" in sources


def test_contract_types():
    contract_types = ethpm.get_manifest("ipfs://testipfs-complex")["contract_types"]
    assert "ComplexNothing" in contract_types
    assert "abi" in contract_types["ComplexNothing"]
    assert contract_types["ComplexNothing"]["source_path"] == "contracts/Complex.sol"


def test_get_deployment_addresses_active_network():
    manifest = ethpm.get_manifest("ipfs://testipfs-complex")
    mainnet_addresses = ethpm.get_deployment_addresses(
        manifest, "ComplexNothing", MAINNET_GENESIS_HASH
    )
    assert len(mainnet_addresses) == 2
    ropsten_addresses = ethpm.get_deployment_addresses(
        manifest, "ComplexNothing", ROPSTEN_GENESIS_HASH
    )
    assert len(ropsten_addresses) == 1
    assert ropsten_addresses[0] not in mainnet_addresses


def test_deployment_addresses_from_dependencies():
    math_manifest = ethpm.get_manifest("ipfs://testipfs-math")
    assert ethpm.get_deployment_addresses(math_manifest, "SafeMath", MAINNET_GENESIS_HASH)

    # math is a dependency of complex, the deployment should not be inherited
    complex_manifest = ethpm.get_manifest("ipfs://testipfs-complex")
    assert not ethpm.get_deployment_addresses(complex_manifest, "SafeMath", MAINNET_GENESIS_HASH)


def test_deployment_addresses_genesis_hash(network):
    manifest = ethpm.get_manifest("ipfs://testipfs-complex")
    ropsten = ethpm.get_deployment_addresses(manifest, "ComplexNothing", ROPSTEN_GENESIS_HASH)
    assert len(ropsten) == 1
    network.connect("ropsten")
    assert ropsten == ethpm.get_deployment_addresses(manifest, "ComplexNothing")
