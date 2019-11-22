#!/usr/bin/python3

import json

from brownie._cli import ethpm as cli_ethpm
from brownie.project import ethpm

ETHPM_CONFIG = {
    "package_name": "testpackage",
    "version": "1.0.0",
    "settings": {"deployment_networks": False, "include_dependencies": False},
}

ERC1319_URI = "erc1319://zeppelin.snakecharmers.eth:1/access@1.0.0"


def test_all(tp_path):
    cli_ethpm._all(tp_path)
    ethpm.install_package(tp_path, ERC1319_URI)
    cli_ethpm._all(tp_path)


def test_list(ipfs_mock, tp_path, mocker):
    mocker.spy(ethpm, "get_installed_packages")
    cli_ethpm._list(tp_path)
    assert ethpm.get_installed_packages.call_count == 1
    ethpm.install_package(tp_path, "ipfs://testipfs-math")
    cli_ethpm._list(tp_path)
    assert ethpm.get_installed_packages.call_count == 2


def test_install(ipfs_mock, tp_path, mocker):
    mocker.spy(ethpm, "install_package")
    cli_ethpm._install(tp_path, ERC1319_URI, "false")
    assert ethpm.install_package.call_count == 1
    assert tp_path.joinpath("contracts/access").exists()


def test_unlink(ipfs_mock, tp_path, mocker):
    ethpm.install_package(tp_path, "ipfs://testipfs-math")
    mocker.spy(ethpm, "remove_package")
    cli_ethpm._unlink(tp_path, "math")
    assert ethpm.remove_package.call_count == 1
    assert tp_path.joinpath("contracts/math").exists()
    cli_ethpm._unlink(tp_path, "math")
    assert ethpm.remove_package.call_count == 2
    assert tp_path.joinpath("contracts/math").exists()


def test_remove(ipfs_mock, tp_path, mocker):
    ethpm.install_package(tp_path, "ipfs://testipfs-math")
    mocker.spy(ethpm, "remove_package")
    cli_ethpm._remove(tp_path, "math")
    assert ethpm.remove_package.call_count == 1
    assert not tp_path.joinpath("contracts/math").exists()
    cli_ethpm._remove(tp_path, "math")
    assert ethpm.remove_package.call_count == 2
    assert not tp_path.joinpath("contracts/math").exists()


def test_create(tp_path, mocker):
    mocker.spy(ethpm, "create_manifest")
    with tp_path.joinpath("ethpm-config.yaml").open("w") as fp:
        json.dump(ETHPM_CONFIG, fp)
    cli_ethpm._create(tp_path)
    assert ethpm.create_manifest.call_count == 1
    assert tp_path.joinpath("manifest.json").exists()
