#!/usr/bin/python3

import shutil
import atexit
import pytest
from pathlib import Path

from brownie import network, project


@pytest.fixture(autouse=True, scope="session")
def session_setup():
    project.load('tests/brownie-test-project')
    network.connect('development')
    atexit.register(_cleanup)


def _cleanup():
    for path in ("build", "reports"):
        path = Path('tests/brownie-test-project').joinpath(path)
        if path.exists():
            shutil.rmtree(str(path))
