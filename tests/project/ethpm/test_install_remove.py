#!/usr/bin/python3

import pytest

from brownie.project import ethpm


def test_install_package(tp_path):
    assert ethpm.get_installed_packages(tp_path) == ([], [])
    ethpm.install_package(tp_path, "ipfs://testipfs-math")
    assert tp_path.joinpath("contracts/math/Math.sol").exists()
    assert ethpm.get_installed_packages(tp_path) == ([("math", "1.0.0")], [])


def test_remove_package(tp_path):
    ethpm.install_package(tp_path, "ipfs://testipfs-math")
    ethpm.remove_package(tp_path, "math", True)
    assert ethpm.get_installed_packages(tp_path) == ([], [])
    assert not tp_path.joinpath("contracts/math/Math.sol").exists()


def test_remove_no_delete(tp_path):
    ethpm.install_package(tp_path, "ipfs://testipfs-math")
    ethpm.remove_package(tp_path, "math", False)
    assert ethpm.get_installed_packages(tp_path) == ([], [])
    assert tp_path.joinpath("contracts/math/Math.sol").exists()


def test_remove_no_delete_re_add(tp_path):
    ethpm.install_package(tp_path, "ipfs://testipfs-math")
    ethpm.remove_package(tp_path, "math", False)
    ethpm.install_package(tp_path, "ipfs://testipfs-math")
    assert tp_path.joinpath("contracts/math/Math.sol").exists()
    assert ethpm.get_installed_packages(tp_path) == ([("math", "1.0.0")], [])


def test_install_and_remove_with_deps(tp_path):
    ethpm.install_package(tp_path, "ipfs://testipfs-complex")
    assert tp_path.joinpath("contracts/math/Math.sol").exists()
    assert ethpm.get_installed_packages(tp_path) == ([("complex", "1.0.0")], [])
    ethpm.install_package(tp_path, "ipfs://testipfs-math")
    assert ethpm.get_installed_packages(tp_path) == ([("complex", "1.0.0"), ("math", "1.0.0")], [])
    ethpm.remove_package(tp_path, "complex", True)
    assert tp_path.joinpath("contracts/math/Math.sol").exists()
    assert not tp_path.joinpath("contracts/complex/Complex.sol").exists()
    assert ethpm.get_installed_packages(tp_path) == ([("math", "1.0.0")], [])


def test_modified(tp_path):
    ethpm.install_package(tp_path, "ipfs://testipfs-math")
    with tp_path.joinpath("contracts/math/Math.sol").open("a") as fp:
        fp.write(" ")
    assert ethpm.get_installed_packages(tp_path) == ([], [("math", "1.0.0")])


def test_modified_overwrite(tp_path):
    ethpm.install_package(tp_path, "ipfs://testipfs-math")
    with tp_path.joinpath("contracts/math/Math.sol").open("a") as fp:
        fp.write(" ")
    with pytest.raises(FileExistsError):
        ethpm.install_package(tp_path, "ipfs://testipfs-complex")
    assert ethpm.get_installed_packages(tp_path) == ([], [("math", "1.0.0")])

    ethpm.install_package(tp_path, "ipfs://testipfs-complex", replace_existing=True)
    assert ethpm.get_installed_packages(tp_path) == ([("complex", "1.0.0"), ("math", "1.0.0")], [])


def test_delete_files(tp_path):
    ethpm.install_package(tp_path, "ipfs://testipfs-utils")

    tp_path.joinpath("contracts/utils/ReentrancyGuard.sol").unlink()
    assert ethpm.get_installed_packages(tp_path) == ([], [("utils", "1.0.0")])

    tp_path.joinpath("contracts/utils/Arrays.sol").unlink()
    tp_path.joinpath("contracts/utils/Address.sol").unlink()
    tp_path.joinpath("contracts/math/Math.sol").unlink()

    assert ethpm.get_installed_packages(tp_path) == ([], [])
    assert not tp_path.joinpath("contracts/utils").exists()
    assert not tp_path.joinpath("contracts/math").exists()
