#!/usr/bin/python3

import pytest

from brownie.project import ethpm

ROPSTEN_GENESIS_HASH = "41941023680923e0fe4d74a34bdac8141f2540e3ae90623718e47d66d1ca4a2d"
MAINNET_GENESIS_HASH = "d4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3"


@pytest.fixture
def tp_path(ipfs_mock, testproject):
    yield testproject._path


def test_get_manifests(ipfs_mock):
    ethpm.get_manifest("ipfs://testipfs-math")
    ethpm.get_manifest("ipfs://testipfs-utils")
    ethpm.get_manifest("ipfs://testipfs-complex")


def test_dependency_paths(ipfs_mock):
    sources = ethpm.get_manifest("ipfs://testipfs-complex")["sources"]
    assert "contracts/Complex.sol" in sources
    assert "contracts/math/SafeMath.sol" in sources
    assert "contracts/utils/Arrays.sol" in sources


def test_contract_types(ipfs_mock):
    contract_types = ethpm.get_manifest("ipfs://testipfs-complex")["contract_types"]
    assert "ComplexNothing" in contract_types
    assert "abi" in contract_types["ComplexNothing"]
    assert contract_types["ComplexNothing"]["source_path"] == "contracts/Complex.sol"


def test_get_deployment_addresses_active_network(ipfs_mock):
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


def test_deployment_addresses_from_dependencies(ipfs_mock):
    math_manifest = ethpm.get_manifest("ipfs://testipfs-math")
    assert ethpm.get_deployment_addresses(math_manifest, "SafeMath", MAINNET_GENESIS_HASH)

    # math is a dependency of complex, the deployment should not be inherited
    complex_manifest = ethpm.get_manifest("ipfs://testipfs-complex")
    assert not ethpm.get_deployment_addresses(complex_manifest, "SafeMath", MAINNET_GENESIS_HASH)


def test_deployment_addresses_genesis_hash(ipfs_mock, network):
    manifest = ethpm.get_manifest("ipfs://testipfs-complex")
    ropsten = ethpm.get_deployment_addresses(manifest, "ComplexNothing", ROPSTEN_GENESIS_HASH)
    assert len(ropsten) == 1
    network.connect("ropsten")
    assert ropsten == ethpm.get_deployment_addresses(manifest, "ComplexNothing")


def test_install_package(tp_path):
    assert ethpm.get_installed_packages(tp_path) == ([], [])
    ethpm.install_package(tp_path, "ipfs://testipfs-math")
    assert tp_path.joinpath("contracts/math/SafeMath.sol").exists()
    assert ethpm.get_installed_packages(tp_path) == ([("math", "1.0.0")], [])


def test_remove_package(tp_path):
    ethpm.install_package(tp_path, "ipfs://testipfs-math")
    ethpm.remove_package(tp_path, "math", True)
    assert ethpm.get_installed_packages(tp_path) == ([], [])
    assert not tp_path.joinpath("contracts/math/SafeMath.sol").exists()


def test_remove_no_delete(tp_path):
    ethpm.install_package(tp_path, "ipfs://testipfs-math")
    ethpm.remove_package(tp_path, "math", False)
    assert ethpm.get_installed_packages(tp_path) == ([], [])
    assert tp_path.joinpath("contracts/math/SafeMath.sol").exists()


def test_remove_no_delete_re_add(tp_path):
    ethpm.install_package(tp_path, "ipfs://testipfs-math")
    ethpm.remove_package(tp_path, "math", False)
    ethpm.install_package(tp_path, "ipfs://testipfs-math")
    assert tp_path.joinpath("contracts/math/SafeMath.sol").exists()
    assert ethpm.get_installed_packages(tp_path) == ([("math", "1.0.0")], [])


def test_install_and_remove_with_deps(tp_path):
    ethpm.install_package(tp_path, "ipfs://testipfs-complex")
    assert tp_path.joinpath("contracts/math/SafeMath.sol").exists()
    assert ethpm.get_installed_packages(tp_path) == ([("complex", "1.0.0")], [])
    ethpm.install_package(tp_path, "ipfs://testipfs-math")
    assert ethpm.get_installed_packages(tp_path) == ([("complex", "1.0.0"), ("math", "1.0.0")], [])
    ethpm.remove_package(tp_path, "complex", True)
    assert tp_path.joinpath("contracts/math/SafeMath.sol").exists()
    assert not tp_path.joinpath("contracts/complex/Complex.sol").exists()
    assert ethpm.get_installed_packages(tp_path) == ([("math", "1.0.0")], [])


def test_modified(tp_path):
    ethpm.install_package(tp_path, "ipfs://testipfs-math")
    with tp_path.joinpath("contracts/math/SafeMath.sol").open("a") as fp:
        fp.write(" ")
    assert ethpm.get_installed_packages(tp_path) == ([], [("math", "1.0.0")])


def test_modified_overwrite(tp_path):
    ethpm.install_package(tp_path, "ipfs://testipfs-math")
    with tp_path.joinpath("contracts/math/SafeMath.sol").open("a") as fp:
        fp.write(" ")
    with pytest.raises(FileExistsError):
        ethpm.install_package(tp_path, "ipfs://testipfs-complex")
    assert ethpm.get_installed_packages(tp_path) == ([], [("math", "1.0.0")])

    ethpm.install_package(tp_path, "ipfs://testipfs-complex", replace_existing=True)
    assert ethpm.get_installed_packages(tp_path) == ([("complex", "1.0.0"), ("math", "1.0.0")], [])


def test_delete_files(tp_path):
    ethpm.install_package(tp_path, "ipfs://testipfs-math")
    tp_path.joinpath("contracts/math/SafeMath.sol").unlink()
    assert ethpm.get_installed_packages(tp_path) == ([], [("math", "1.0.0")])
    tp_path.joinpath("contracts/math/Math.sol").unlink()
    assert ethpm.get_installed_packages(tp_path) == ([], [])
    assert not tp_path.joinpath("contracts/math").exists()
