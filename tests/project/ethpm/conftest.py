#!/usr/bin/python3

import json

import pytest

from brownie import network, project, web3
from brownie.project import ethpm


@pytest.fixture(autouse=True)
def ipfs_setup(ipfs_mock):
    pass


@pytest.fixture
def tp_path(testproject):
    yield testproject._path


@pytest.fixture
def dep_project(testproject):
    # this bit of hackiness is needed to trigger a recompile of the project
    ethpm.install_package(testproject._path, "ipfs://testipfs-utils")
    testproject.close()
    yield project.load(testproject._path)


@pytest.fixture
def deployments(testproject):
    path = testproject._path.joinpath("build/deployments/ropsten")
    path.mkdir(exist_ok=True)
    with path.joinpath("0xBcd0a9167015Ee213Ba01dAff79d60CD221B0cAC.json").open("w") as fp:
        json.dump(testproject.BrownieTester._build, fp)

    path = testproject._path.joinpath("build/deployments/mainnet")
    path.mkdir(exist_ok=True)
    with path.joinpath("0xdAC17F958D2ee523a2206206994597C13D831ec7.json").open("w") as fp:
        json.dump(testproject.BrownieTester._build, fp)
    with path.joinpath("0xB8c77482e45F1F44dE1745F52C74426C631bDD52.json").open("w") as fp:
        json.dump(testproject.BrownieTester._build, fp)


@pytest.fixture(scope="session")
def ropsten_uri():
    prev = network.show_active()
    if prev:
        network.disconnect(False)
    network.connect("ropsten")
    uri = web3.chain_uri
    network.disconnect(False)
    if prev:
        network.connect(prev)
    yield uri


@pytest.fixture(scope="session")
def mainnet_uri():
    prev = network.show_active()
    if prev:
        network.disconnect(False)
    network.connect("mainnet")
    uri = web3.chain_uri
    network.disconnect(False)
    if prev:
        network.connect(prev)
    yield uri
