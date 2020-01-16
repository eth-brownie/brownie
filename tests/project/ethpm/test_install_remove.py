#!/usr/bin/python3

import pytest

from brownie.project import ethpm


def test_install_package(np_path):
    assert ethpm.get_installed_packages(np_path) == ([], [])
    ethpm.install_package(np_path, "ipfs://testipfs-math")
    assert np_path.joinpath("contracts/math/Math.sol").exists()
    assert ethpm.get_installed_packages(np_path) == ([("math", "1.0.0")], [])


def test_remove_package(np_path):
    ethpm.install_package(np_path, "ipfs://testipfs-math")
    ethpm.remove_package(np_path, "math", True)
    assert ethpm.get_installed_packages(np_path) == ([], [])
    assert not np_path.joinpath("contracts/math/Math.sol").exists()


def test_remove_no_delete(np_path):
    ethpm.install_package(np_path, "ipfs://testipfs-math")
    ethpm.remove_package(np_path, "math", False)
    assert ethpm.get_installed_packages(np_path) == ([], [])
    assert np_path.joinpath("contracts/math/Math.sol").exists()


def test_remove_no_delete_re_add(np_path):
    ethpm.install_package(np_path, "ipfs://testipfs-math")
    ethpm.remove_package(np_path, "math", False)
    ethpm.install_package(np_path, "ipfs://testipfs-math")
    assert np_path.joinpath("contracts/math/Math.sol").exists()
    assert ethpm.get_installed_packages(np_path) == ([("math", "1.0.0")], [])


def test_install_and_remove_with_deps(np_path):
    ethpm.install_package(np_path, "ipfs://testipfs-complex")
    assert np_path.joinpath("contracts/math/Math.sol").exists()
    assert ethpm.get_installed_packages(np_path) == ([("complex", "1.0.0")], [])
    ethpm.install_package(np_path, "ipfs://testipfs-math")
    assert ethpm.get_installed_packages(np_path) == ([("complex", "1.0.0"), ("math", "1.0.0")], [])
    ethpm.remove_package(np_path, "complex", True)
    assert np_path.joinpath("contracts/math/Math.sol").exists()
    assert not np_path.joinpath("contracts/complex/Complex.sol").exists()
    assert ethpm.get_installed_packages(np_path) == ([("math", "1.0.0")], [])


def test_modified(np_path):
    ethpm.install_package(np_path, "ipfs://testipfs-math")
    with np_path.joinpath("contracts/math/Math.sol").open("a") as fp:
        fp.write(" ")
    assert ethpm.get_installed_packages(np_path) == ([], [("math", "1.0.0")])


def test_modified_overwrite(np_path):
    ethpm.install_package(np_path, "ipfs://testipfs-math")
    with np_path.joinpath("contracts/math/Math.sol").open("a") as fp:
        fp.write(" ")
    with pytest.raises(FileExistsError):
        ethpm.install_package(np_path, "ipfs://testipfs-complex")
    assert ethpm.get_installed_packages(np_path) == ([], [("math", "1.0.0")])

    ethpm.install_package(np_path, "ipfs://testipfs-complex", replace_existing=True)
    assert ethpm.get_installed_packages(np_path) == ([("complex", "1.0.0"), ("math", "1.0.0")], [])


def test_delete_files(np_path):
    ethpm.install_package(np_path, "ipfs://testipfs-utils")

    np_path.joinpath("contracts/utils/ReentrancyGuard.sol").unlink()
    assert ethpm.get_installed_packages(np_path) == ([], [("utils", "1.0.0")])

    np_path.joinpath("contracts/utils/Arrays.sol").unlink()
    np_path.joinpath("contracts/utils/Address.sol").unlink()
    np_path.joinpath("contracts/math/Math.sol").unlink()

    assert ethpm.get_installed_packages(np_path) == ([], [])
    assert not np_path.joinpath("contracts/utils").exists()
    assert not np_path.joinpath("contracts/math").exists()


def test_vyper_package_json_interface(newproject):
    ethpm.install_package(newproject._path, "ipfs://testipfs-vyper")
    newproject.load()
    assert newproject._path.joinpath("interfaces/Bar.json").exists()
