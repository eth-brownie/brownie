#!/usr/bin/python3

import shutil
from pathlib import Path
import pytest

from brownie import project, network


@pytest.fixture(scope="module", autouse=True)
def setup(projectpath):
    project.close(False)
    network.disconnect()
    yield
    project.close(False)
    project.load(projectpath)
    if not network.is_connected():
        network.connect()


def test_run_tests(testdir, projectpath):

    testdir.plugins.extend(['pytest-brownie', 'pytest-cov'])

    dest_folder = Path(testdir.tmpdir)
    for p in projectpath.glob('*'):
        dest = dest_folder.joinpath(p.name)
        if p.is_dir():
            shutil.copytree(str(p), dest)
        else:
            shutil.copy(str(p), dest)

    testdir.runpytest("tests")
