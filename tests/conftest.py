#!/usr/bin/python3

import shutil
import pytest
from _pytest.monkeypatch import MonkeyPatch  # derive_importpath


import brownie
from brownie import network, project
from brownie.test import coverage
from brownie._config import ARGV

pytest_plugins = 'pytester'


def pytest_sessionstart():

    # github blocks travis from their API, so this method is patched for the entire session
    monkeypatch_session = MonkeyPatch()
    monkeypatch_session.setattr(
        "solcx.get_available_solc_versions",
        lambda: ['v0.5.10', 'v0.5.9', 'v0.5.8', 'v0.5.7', 'v0.4.25', 'v0.4.24', 'v0.4.22']
    )


# project / network fixtures

@pytest.fixture(scope="session")
def _project_factory(tmp_path_factory):
    path = tmp_path_factory.mktemp('base')
    path.rmdir()
    shutil.copytree('tests/brownie-test-project', path)
    shutil.copyfile('brownie/data/config.json', path.joinpath('brownie-config.json'))
    p = project.load(path, 'TestProject')
    p.close()
    return path


@pytest.fixture
def testproject(_project_factory, tmp_path):
    tmp_path.rmdir()
    shutil.copytree(_project_factory, tmp_path)
    p = project.load(tmp_path, 'TestProject')
    yield p
    p.close(False)


@pytest.fixture
def devnetwork():
    network.connect('development')
    yield
    network.rpc.reset()
    network.disconnect(False)


# brownie object fixtures

@pytest.fixture
def accounts(devnetwork):
    return network.accounts


@pytest.fixture
def history():
    return network.history


@pytest.fixture
def rpc(devnetwork):
    return network.rpc


@pytest.fixture
def web3():
    return network.web3


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


@pytest.fixture
def console_mode(argv):
    argv['cli'] = "console"


@pytest.fixture
def test_mode(argv):
    argv['cli'] = "test"


@pytest.fixture
def coverage_mode(argv, test_mode):
    cov_eval = coverage._coverage_eval
    cached = coverage._cached
    coverage._coverage_eval = {}
    coverage._cached = {}
    argv['coverage'] = True
    argv['always_transact'] = True
    yield
    coverage._coverage_eval = cov_eval
    coverage._cached = cached


# contract fixtures

@pytest.fixture
def BrownieTester(testproject, devnetwork):
    return testproject.BrownieTester


@pytest.fixture
def tester(BrownieTester, accounts):
    c = BrownieTester.deploy(True, {'from': accounts[0]})
    return c


# @pytest.fixture(scope="session")
# def projectpath():
#     yield Path(__file__).parent.joinpath('brownie-test-project')


# @pytest.fixture
# def testproject():
#     return project.BrownieTestProject


# @pytest.fixture
# def Token(testproject):
#     return testproject.Token


# @pytest.fixture(scope="module")
# def tester():
#     network.rpc.reset()
#     project.BrownieTestProject.UnlinkedLib.deploy({'from': accounts[0]})
#     contract = project.BrownieTestProject.BrownieTester.deploy({'from': accounts[0]})
#     yield contract
#     network.rpc.reset()


# @pytest.fixture
# def clean_network():
#     network.rpc.reset()
#     yield
#     network.rpc.reset()


# @pytest.fixture
# def testpath(tmpdir):
#     original_path = os.getcwd()
#     os.chdir(tmpdir)
#     yield tmpdir
#     os.chdir(original_path)


# class MethodWatcher:

#     '''Extension of pytest's monkeypatch. Wraps around methods so we can check
#     if they were called during the execution of a test.'''

#     def __init__(self, monkeypatch):
#         self.monkeypatch = monkeypatch
#         self.targets = {}

#     def assert_called(self):
#         assert False not in self.targets.values()

#     def assert_not_called(self):
#         assert set(self.targets.values()) == {False}

#     def watch(self, *targets):
#         for t in targets:
#             name, target = derive_importpath(t, True)
#             key = f"{target}.{name}"
#             self.targets[key] = False
#             fn = functools.partial(self._catch, key, getattr(target, name))
#             self.monkeypatch.setattr(target, name, fn)

#     def _catch(self, key, fn, *args, **kwargs):
#         fn(*args, **kwargs)
#         self.targets[key] = True

#     def reset(self):
#         self.targets = dict((i, False) for i in self.targets)


# @pytest.fixture
# def methodwatch(monkeypatch):
#     yield MethodWatcher(monkeypatch)
