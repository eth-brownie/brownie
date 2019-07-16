#!/usr/bin/python3

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
