#!/usr/bin/python3

import json

import pytest

from brownie._cli import ethpm as cli_ethpm
from brownie.project import ethpm

ETHPM_CONFIG = {
    "package_name": "testpackage",
    "version": "1.0.0",
    "settings": {"deployment_networks": False, "include_dependencies": False},
}

ERC1319_URI = "erc1319://zeppelin.snakecharmers.eth:1/access@1.0.0"


def test_all(np_path):
    cli_ethpm._all(np_path)
    ethpm.install_package(np_path, ERC1319_URI)
    cli_ethpm._all(np_path)


def test_list(ipfs_mock, np_path, mocker):
    mocker.spy(ethpm, "get_installed_packages")
    cli_ethpm._list(np_path)
    assert ethpm.get_installed_packages.call_count == 1
    ethpm.install_package(np_path, "ipfs://testipfs-math")
    cli_ethpm._list(np_path)
    assert ethpm.get_installed_packages.call_count == 2


def test_list_with_modified_packages(ipfs_mock, np_path, mocker, monkeypatch):
    monkeypatch.setattr(
        "brownie.project.ethpm.get_installed_packages", lambda project_path: [[], ["P1"]]
    )
    cli_ethpm._list(np_path)
    assert True


def test_install(ipfs_mock, np_path, mocker):
    mocker.spy(ethpm, "install_package")
    cli_ethpm._install(np_path, ERC1319_URI, "false")
    assert ethpm.install_package.call_count == 1
    assert np_path.joinpath("contracts/access").exists()


def test_install_value_error(ipfs_mock, np_path, mocker):
    mocker.spy(ethpm, "install_package")

    with pytest.raises(ValueError):
        cli_ethpm._install(np_path, ERC1319_URI, "foobar")


def test_unlink(ipfs_mock, np_path, mocker):
    ethpm.install_package(np_path, "ipfs://testipfs-math")
    mocker.spy(ethpm, "remove_package")
    cli_ethpm._unlink(np_path, "math")
    assert ethpm.remove_package.call_count == 1
    assert np_path.joinpath("contracts/math").exists()
    cli_ethpm._unlink(np_path, "math")
    assert ethpm.remove_package.call_count == 2
    assert np_path.joinpath("contracts/math").exists()


def test_remove(ipfs_mock, np_path, mocker):
    ethpm.install_package(np_path, "ipfs://testipfs-math")
    mocker.spy(ethpm, "remove_package")
    cli_ethpm._remove(np_path, "math")
    assert ethpm.remove_package.call_count == 1
    assert not np_path.joinpath("contracts/math").exists()
    cli_ethpm._remove(np_path, "math")
    assert ethpm.remove_package.call_count == 2
    assert not np_path.joinpath("contracts/math").exists()


def test_create(np_path, mocker):
    mocker.spy(ethpm, "create_manifest")
    with np_path.joinpath("ethpm-config.yaml").open("w") as fp:
        json.dump(ETHPM_CONFIG, fp)
    cli_ethpm._create(np_path)
    assert ethpm.create_manifest.call_count == 1
    assert np_path.joinpath("manifest.json").exists()


def raise_exception(e):
    raise e


def test_exceptions(np_path, monkeypatch):
    monkeypatch.setattr(
        "brownie.project.ethpm.create_manifest",
        lambda project_path, package_config: raise_exception(Exception("foobar")),
    )

    with np_path.joinpath("ethpm-config.yaml").open("w") as fp:
        json.dump(ETHPM_CONFIG, fp)
    cli_ethpm._create(np_path)

    assert not np_path.joinpath("manifest.json").exists()
