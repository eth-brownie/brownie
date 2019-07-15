#!/usr/bin/python3

import functools
import shutil
from pathlib import Path
import pytest

from brownie import project


@pytest.fixture(scope="module", autouse=True)
def module_setup(projectpath):
    yield
    project.load(projectpath)


@pytest.fixture(autouse=True)
def setup(monkeypatch, testdir, projectpath):
    project.close(False)
    monkeypatch.setattr('brownie.network.connect', lambda k: None)
    testdir.plugins.extend(['pytest-brownie', 'pytest-cov'])
    dest_folder = Path(testdir.tmpdir)
    for path in projectpath.glob('*'):
        dest = dest_folder.joinpath(path.name)
        if path.is_dir():
            shutil.copytree(path, dest)
        else:
            shutil.copy(path, dest)
    yield
    project.close(False)


class MethodCallTester:

    def __init__(self, monkeypatch):
        self.monkeypatch = monkeypatch
        self.targets = {}

    def __bool__(self):
        return False not in self.targets.values()

    def patch(self, obj, attr):
        key = f"{obj.__name__}.{attr}"
        self.targets[key] = False
        fn = functools.partial(self.catch, key, getattr(obj, attr))

        self.monkeypatch.setattr(obj, attr, fn)

    def catch(self, key, fn, *args, **kwargs):
        self.targets[key] = True

    def reset(self):
        self.targets = dict((i, False) for i in self.targets)


@pytest.fixture
def callcatch(monkeypatch):
    yield MethodCallTester(monkeypatch)
