#!/usr/bin/python3

import shutil
import pytest
from pathlib import Path

from brownie import accounts, network, project
from brownie._config import ARGV


@pytest.fixture(autouse=True, scope="session")
def session_setup():
    project.load('tests/brownie-test-project')
    network.connect('development')
    yield
    for path in ("build", "reports"):
        path = Path('tests/brownie-test-project').joinpath(path)
        if path.exists():
            shutil.rmtree(str(path))


@pytest.fixture(scope="module")
def tester():
    network.rpc.reset()
    project.UnlinkedLib.deploy({'from': accounts[0]})
    yield project.BrownieTester.deploy({'from': accounts[0]})
    network.rpc.reset()


@pytest.fixture(scope="module")
def token():
    network.rpc.reset()
    yield project.Token.deploy("TST", "Test Token", 18, 1000000, {'from': accounts[0]})
    network.rpc.reset()


@pytest.fixture(scope="function")
def console_mode():
    ARGV['cli'] = "console"
    yield
    ARGV['cli'] = False


@pytest.fixture(scope="function")
def test_mode():
    ARGV['cli'] = "test"
    yield
    ARGV['cli'] = False


@pytest.fixture(scope="function")
def coverage_mode():
    ARGV['cli'] = "test"
    ARGV['coverage'] = True
    yield
    ARGV['cli'] = False
    ARGV['coverage'] = False


@pytest.fixture(scope="function")
def clean_network():
    network.rpc.reset()
    yield
    network.rpc.reset()
