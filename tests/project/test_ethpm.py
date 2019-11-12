#!/usr/bin/python3

from brownie.project.ethpm import get_deployment_addresses, get_manifest

ROPSTEN_GENESIS_HASH = "41941023680923e0fe4d74a34bdac8141f2540e3ae90623718e47d66d1ca4a2d"
MAINNET_GENESIS_HASH = "d4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3"


def test_get_manifests(ipfs_mock):
    get_manifest("ipfs://testipfs-math")
    get_manifest("ipfs://testipfs-utils")
    get_manifest("ipfs://testipfs-complex")


def test_dependency_paths(ipfs_mock):
    sources = get_manifest("ipfs://testipfs-complex")["sources"]
    assert "contracts/Complex.sol" in sources
    assert "contracts/math/SafeMath.sol" in sources
    assert "contracts/utils/Arrays.sol" in sources


def test_contract_types(ipfs_mock):
    contract_types = get_manifest("ipfs://testipfs-complex")["contract_types"]
    assert "ComplexNothing" in contract_types
    assert "abi" in contract_types["ComplexNothing"]
    assert contract_types["ComplexNothing"]["source_path"] == "contracts/Complex.sol"


def test_get_deployment_addresses_active_network(ipfs_mock):
    manifest = get_manifest("ipfs://testipfs-complex")
    mainnet_addresses = get_deployment_addresses(manifest, "ComplexNothing", MAINNET_GENESIS_HASH)
    assert len(mainnet_addresses) == 2
    ropsten_addresses = get_deployment_addresses(manifest, "ComplexNothing", ROPSTEN_GENESIS_HASH)
    assert len(ropsten_addresses) == 1
    assert ropsten_addresses[0] not in mainnet_addresses


def test_deployment_addresses_from_dependencies(ipfs_mock):
    math_manifest = get_manifest("ipfs://testipfs-math")
    assert get_deployment_addresses(math_manifest, "SafeMath", MAINNET_GENESIS_HASH)

    # math is a dependency of complex, the deployment should not be inherited
    complex_manifest = get_manifest("ipfs://testipfs-complex")
    assert not get_deployment_addresses(complex_manifest, "SafeMath", MAINNET_GENESIS_HASH)


def test_deployment_addresses_genesis_hash(ipfs_mock, network):
    manifest = get_manifest("ipfs://testipfs-complex")
    ropsten = get_deployment_addresses(manifest, "ComplexNothing", ROPSTEN_GENESIS_HASH)
    assert len(ropsten) == 1
    network.connect("ropsten")
    assert ropsten == get_deployment_addresses(manifest, "ComplexNothing")
