#!/usr/bin/python3

import json

import pytest

from brownie._cli import ethpm as cli_ethpm
from brownie.exceptions import UnknownAccount
from brownie.project import ethpm

ETHPM_CONFIG = {
    "package_name": "testpackage",
    "version": "1.0.0",
    "settings": {"deployment_networks": False, "include_dependencies": False},
}


@pytest.fixture
def registry(ipfs_mock, testproject, accounts, monkeypatch):
    monkeypatch.setattr("brownie._cli.ethpm.network.connect", lambda k: True)
    with testproject._path.joinpath("ethpm-config.yaml").open("w") as fp:
        json.dump(ETHPM_CONFIG, fp)
    yield testproject.PackageRegistry.deploy({"from": accounts[0]})


@pytest.fixture(autouse=True)
def mocker_spy(mocker):
    mocker.spy(ethpm, "create_manifest")
    mocker.spy(ethpm, "verify_manifest")
    mocker.spy(ethpm, "release_package")


def test_release_localaccount(registry, accounts, tp_path, monkeypatch, tmpdir):

    monkeypatch.setattr("brownie.network.account.getpass", lambda x: "")
    a = accounts.add()
    a.save(tmpdir + "/release_tester.json")
    accounts[0].transfer(a, "1 ether")
    accounts._reset()

    cli_ethpm._release(tp_path, registry.address, tmpdir + "/release_tester.json")
    assert ethpm.create_manifest.call_count == 1
    assert ethpm.verify_manifest.call_count == 1
    assert ethpm.release_package.call_count == 1
    id_ = registry.getReleaseId("testpackage", "1.0.0")
    assert registry.getReleaseData(id_)[-1] == ethpm.create_manifest.spy_return[1]


def test_release_account(registry, accounts, tp_path):

    cli_ethpm._release(tp_path, registry.address, accounts[0].address)
    assert ethpm.create_manifest.call_count == 1
    assert ethpm.verify_manifest.call_count == 1
    assert ethpm.release_package.call_count == 1
    id_ = registry.getReleaseId("testpackage", "1.0.0")
    assert registry.getReleaseData(id_)[-1] == ethpm.create_manifest.spy_return[1]


def test_release_unknown_account(registry, accounts, tp_path):
    with pytest.raises(UnknownAccount):
        cli_ethpm._release(tp_path, registry.address, "0x2a8638962741B4fA728983A6C0F57080522aa73a")


def raise_exception(e):
    raise e


def test_exceptions(registry, accounts, tp_path, monkeypatch):
    monkeypatch.setattr(
        "brownie.project.ethpm.release_package",
        lambda registry_address, account, package_name, version, uri: raise_exception(
            Exception("foobar")
        ),
    )

    cli_ethpm._release(tp_path, registry.address, accounts[0].address)
    assert ethpm.create_manifest.call_count == 1
    assert ethpm.verify_manifest.call_count == 0
