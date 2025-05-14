#!/usr/bin/python3

import json


def test_persist_load_unload(testproject, connect_to_mainnet):
    testproject.BrownieTester.at("0xdAC17F958D2ee523a2206206994597C13D831ec7")
    testproject.close()
    testproject.load()
    assert len(testproject.BrownieTester) == 1


def test_delete(testproject, network, connect_to_mainnet):
    testproject.BrownieTester.at("0xdAC17F958D2ee523a2206206994597C13D831ec7")
    testproject.BrownieTester.at("0xB8c77482e45F1F44dE1745F52C74426C631bDD52")
    _disconnect(network)
    _reconnect(network)
    del testproject.BrownieTester[0]
    _disconnect(network)
    _reconnect(network)
    assert len(testproject.BrownieTester) == 1
    assert testproject.BrownieTester[0].address == "0xB8c77482e45F1F44dE1745F52C74426C631bDD52"


def test_changed_name(testproject, network, connect_to_mainnet):
    c = testproject.BrownieTester.at("0xdAC17F958D2ee523a2206206994597C13D831ec7")
    testproject.BrownieTester.at("0xB8c77482e45F1F44dE1745F52C74426C631bDD52")
    build_json = c._build
    _disconnect(network)
    build_json["contractName"] = "PotatoTester"

    path = testproject._path.joinpath(
        "build/deployments/1/0xdAC17F958D2ee523a2206206994597C13D831ec7.json"
    )
    with path.open("w") as fp:
        json.dump(build_json, fp)

    _reconnect(network)
    assert not path.exists()
    assert len(testproject.BrownieTester) == 1
    assert testproject.BrownieTester[0].address == "0xB8c77482e45F1F44dE1745F52C74426C631bDD52"


def _disconnect(network) -> None:
    # Just a helper to deal with intermittent errs that aren't relevant to our tests
    try:
        network.disconnect(False)
    except ConnectionError:
        # `ConnectionError: Not connected to any network`
        # This happens in the test runners sometimes, we're not too concerned with why or how to fix.
        # It's probably just a silly race condition due to parallel testing.
        pass


def _reconnect(network) -> None:
    # I expect an intermittent err here eventually so I'm making this handler now.
    network.connect("mainnet")
