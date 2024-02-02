#!/usr/bin/python3

import json


def test_persist_load_unload(testproject, network):
    network.connect("mainnet")
    testproject.BrownieTester.at("0xdAC17F958D2ee523a2206206994597C13D831ec7")
    testproject.close()
    testproject.load()
    assert len(testproject.BrownieTester) == 1


def test_delete(testproject, network):
    network.connect("mainnet")
    testproject.BrownieTester.at("0xdAC17F958D2ee523a2206206994597C13D831ec7")
    testproject.BrownieTester.at("0xB8c77482e45F1F44dE1745F52C74426C631bDD52")
    network.disconnect(False)
    network.connect("mainnet")
    del testproject.BrownieTester[0]
    network.disconnect(False)
    network.connect("mainnet")
    assert len(testproject.BrownieTester) == 1
    assert testproject.BrownieTester[0].address == "0xB8c77482e45F1F44dE1745F52C74426C631bDD52"


def test_changed_name(testproject, network):
    network.connect("mainnet")
    c = testproject.BrownieTester.at("0xdAC17F958D2ee523a2206206994597C13D831ec7")
    testproject.BrownieTester.at("0xB8c77482e45F1F44dE1745F52C74426C631bDD52")
    build_json = c._build
    network.disconnect(False)
    build_json["contractName"] = "PotatoTester"

    path = testproject._path.joinpath(
        "build/deployments/1/0xdAC17F958D2ee523a2206206994597C13D831ec7.json"
    )
    with path.open("w") as fp:
        json.dump(build_json, fp)

    network.connect("mainnet")
    assert not path.exists()
    assert len(testproject.BrownieTester) == 1
    assert testproject.BrownieTester[0].address == "0xB8c77482e45F1F44dE1745F52C74426C631bDD52"
