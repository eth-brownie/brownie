#!/usr/bin/python3

import functools
import os
import shutil
from pathlib import Path
import psutil
import pytest
from _pytest.monkeypatch import derive_importpath
import sys

from brownie import accounts, network, project
from brownie._config import ARGV

pytest_plugins = 'pytester'


@pytest.fixture(autouse=True, scope="session")
def session_setup():
    network.connect('development')
    project.load('tests/brownie-test-project')
    yield
    for path in ("build", "reports"):
        path = Path('tests/brownie-test-project').joinpath(path)
        if path.exists():
            shutil.rmtree(str(path))
    # clean up any child processes so travis doesn't time out
    if sys.platform == "win32":
        for proc in list(psutil.process_iter()):
            try:
                if proc.name() in ("node.exe", "cmd.exe"):
                    proc.kill()
            except psutil.AccessDenied:
                pass


@pytest.fixture(scope="session")
def projectpath():
    yield Path(__file__).parent.joinpath('brownie-test-project')


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


@pytest.fixture
def noload(projectpath):
    project.close(False)
    yield
    project.close(False)
    project.load(projectpath)


@pytest.fixture
def console_mode():
    ARGV['cli'] = "console"
    yield
    ARGV['cli'] = False


@pytest.fixture
def test_mode():
    ARGV['cli'] = "test"
    yield
    ARGV['cli'] = False


@pytest.fixture
def coverage_mode():
    ARGV['cli'] = "test"
    ARGV['coverage'] = True
    ARGV['always_transact'] = True
    yield
    ARGV['cli'] = False
    ARGV['coverage'] = False
    ARGV['always_transact'] = False


@pytest.fixture
def clean_network():
    network.rpc.reset()
    yield
    network.rpc.reset()


@pytest.fixture
def testpath(tmpdir):
    original_path = os.getcwd()
    os.chdir(tmpdir)
    yield tmpdir
    os.chdir(original_path)


class MethodWatcher:

    '''Extension of pytest's monkeypath. Wraps around methods so we can check
    if they were called during the execution of a test.'''

    def __init__(self, monkeypatch):
        self.monkeypatch = monkeypatch
        self.targets = {}

    def assert_called(self):
        assert False not in self.targets.values()

    def assert_not_called(self):
        assert set(self.targets.values()) == {False}

    def watch(self, *targets):
        for t in targets:
            name, target = derive_importpath(t, True)
            key = f"{target}.{name}"
            self.targets[key] = False
            fn = functools.partial(self._catch, key, getattr(target, name))
            self.monkeypatch.setattr(target, name, fn)

    def _catch(self, key, fn, *args, **kwargs):
        fn(*args, **kwargs)
        self.targets[key] = True

    def reset(self):
        self.targets = dict((i, False) for i in self.targets)


@pytest.fixture
def methodwatch(monkeypatch):
    yield MethodWatcher(monkeypatch)
