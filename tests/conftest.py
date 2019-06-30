#!/usr/bin/python3

import os
import shutil
import pytest
from pathlib import Path

from brownie import accounts, network, project
from brownie._config import ARGV


@pytest.fixture(autouse=True, scope="session")
def session_setup():
    network.connect('development')
    project.load('tests/brownie-test-project')
    yield
    for path in ("build", "reports"):
        path = Path('tests/brownie-test-project').joinpath(path)
        if path.exists():
            shutil.rmtree(str(path))


@pytest.fixture(scope="function")
def noload():
    project.close(False)
    yield
    project.close(False)
    project.load(Path(__file__).parent.joinpath('brownie-test-project'))


@pytest.fixture(scope="module")
def tester():
    network.rpc.reset()
    project.UnlinkedLib.deploy({'from': accounts[0]})
    contract = project.BrownieTester.deploy({'from': accounts[0]})
    yield contract
    network.rpc.reset()


@pytest.fixture(scope="module")
def token():
    network.rpc.reset()
    contract = project.Token.deploy("TST", "Test Token", 18, 1000000, {'from': accounts[0]})
    yield contract
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
    ARGV['always_transact'] = True
    yield
    ARGV['cli'] = False
    ARGV['coverage'] = False
    ARGV['always_transact'] = False


@pytest.fixture(scope="function")
def clean_network():
    network.rpc.reset()
    yield
    network.rpc.reset()


@pytest.fixture(scope="function")
def testpath(tmpdir):
    original_path = os.getcwd()
    os.chdir(tmpdir)
    yield tmpdir
    os.chdir(original_path)
