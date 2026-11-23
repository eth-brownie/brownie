#!/usr/bin/python3

import json


def test_persist_load_unload(testproject, BrownieTester, devnetwork, accounts, config):
    config.settings["dev_deployment_artifacts"] = True

    contract = BrownieTester.deploy(True, {"from": accounts[0]})
    _reload(testproject)

    assert len(testproject.BrownieTester) == 1, testproject.BrownieTester
    assert testproject.BrownieTester[0].address == contract.address


def test_delete(testproject, BrownieTester, devnetwork, accounts, config):
    config.settings["dev_deployment_artifacts"] = True

    BrownieTester.deploy(True, {"from": accounts[0]})
    second = BrownieTester.deploy(True, {"from": accounts[0]})
    _reload(testproject)

    del testproject.BrownieTester[0]
    _reload(testproject)

    assert len(testproject.BrownieTester) == 1, testproject.BrownieTester
    assert testproject.BrownieTester[0].address == second.address


def test_changed_name(testproject, BrownieTester, devnetwork, accounts, config):
    config.settings["dev_deployment_artifacts"] = True

    contract = BrownieTester.deploy(True, {"from": accounts[0]})
    second = BrownieTester.deploy(True, {"from": accounts[0]})

    path = testproject._path.joinpath(f"build/deployments/dev/{contract.address}.json")
    with path.open() as fp:
        build_json = json.load(fp)
    build_json["contractName"] = "PotatoTester"
    with path.open("w") as fp:
        json.dump(build_json, fp)

    _reload(testproject)

    assert not path.exists()
    assert len(testproject.BrownieTester) == 1, testproject.BrownieTester
    assert testproject.BrownieTester[0].address == second.address


def _reload(testproject) -> None:
    testproject.close()
    testproject.load()
