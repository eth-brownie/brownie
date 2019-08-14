#!/usr/bin/python3

import os
from pathlib import Path
import shutil
import pytest
from _pytest.monkeypatch import MonkeyPatch  # derive_importpath

import brownie
from brownie._config import ARGV

pytest_plugins = 'pytester'


def pytest_sessionstart():
    # travis cannot call github ethereum/solidity API, so this method is patched
    monkeypatch_session = MonkeyPatch()
    monkeypatch_session.setattr(
        "solcx.get_available_solc_versions",
        lambda: ['v0.5.10', 'v0.5.9', 'v0.5.8', 'v0.5.7', 'v0.4.25', 'v0.4.24', 'v0.4.22']
    )


@pytest.fixture(scope="session")
def _project_factory(tmp_path_factory):
    path = tmp_path_factory.mktemp('base')
    path.rmdir()
    shutil.copytree('tests/brownie-test-project', path)
    shutil.copyfile('brownie/data/config.json', path.joinpath('brownie-config.json'))
    p = brownie.project.load(path, 'TestProject')
    p.close()
    return path


def _copy_all(src_folder, dest_folder):
    for path in Path(src_folder).glob('*'):
        dest_path = Path(dest_folder).joinpath(path.name)
        if path.is_dir():
            shutil.copytree(path, dest_path)
        else:
            shutil.copy(path, dest_path)

# project fixtures

# creates a temporary folder and sets it as the working directory
@pytest.fixture
def project(tmp_path):
    original_path = os.getcwd()
    os.chdir(tmp_path)
    yield brownie.project
    os.chdir(original_path)
    for p in brownie.project.get_loaded_projects():
        p.close(False)

# copies the tester project into a temporary folder, loads it, and yields a Project object
@pytest.fixture
def testproject(_project_factory, project, tmp_path):
    _copy_all(_project_factory, tmp_path)
    return brownie.project.load(tmp_path, 'TestProject')


@pytest.fixture
def otherproject(testproject):
    return brownie.project.load(testproject._project_path, 'OtherProject')

# setup for pytest-brownie plugin testing
@pytest.fixture
def plugintester(_project_factory, project, testdir, request, rpc, monkeypatch):
    brownie.test.coverage.clear()
    brownie.network.connect()
    monkeypatch.setattr('brownie.network.connect', lambda k: None)
    testdir.plugins.extend(['pytest-brownie', 'pytest-cov'])
    _copy_all(_project_factory, testdir.tmpdir)
    test_source = getattr(request.module, 'test_source', None)
    if test_source:
        testdir.makepyfile(test_source)
    yield testdir
    brownie.network.disconnect()

# launches and connects to ganache, yields the brownie.network module
@pytest.fixture
def devnetwork(network, rpc):
    if brownie.network.is_connected():
        brownie.network.disconnect(False)
    brownie.network.connect('development')
    yield brownie.network
    if rpc.is_active():
        rpc.reset()


# brownie object fixtures

@pytest.fixture
def accounts(devnetwork):
    return brownie.network.accounts


@pytest.fixture
def history():
    return brownie.network.history


@pytest.fixture
def network():
    yield brownie.network
    if brownie.network.is_connected():
        brownie.network.disconnect(False)


@pytest.fixture
def rpc():
    return brownie.network.rpc


@pytest.fixture
def web3():
    return brownie.network.web3


# configuration fixtures
# changes to config or argv are reverted during teardown

@pytest.fixture
def config(testproject):
    return brownie.config


@pytest.fixture
def argv():
    initial = {}
    initial.update(ARGV)
    yield ARGV
    ARGV.clear()
    ARGV.update(initial)


# cli mode fixtures

@pytest.fixture
def console_mode(argv):
    argv['cli'] = "console"


@pytest.fixture
def test_mode(argv):
    argv['cli'] = "test"


@pytest.fixture
def coverage_mode(argv, test_mode):
    brownie.test.coverage.clear()
    argv['coverage'] = True
    argv['always_transact'] = True


# contract fixtures

@pytest.fixture
def BrownieTester(testproject, devnetwork):
    return testproject.BrownieTester


@pytest.fixture
def tester(BrownieTester, accounts):
    c = BrownieTester.deploy(True, {'from': accounts[0]})
    return c
