#!/usr/bin/python3

import shutil
import atexit
import pytest
from pathlib import Path

from brownie import project


@pytest.fixture(autouse=True, scope="session")
def session_setup():
    project.load('tests/brownie-test-project')
    assert hasattr(project, 'Token'), "Did not initialize Token ContractContainer"
    assert hasattr(project, 'SafeMath'), "Did not initialize SafeMath ContractContainer"
    assert not hasattr(project, "TokenABC")
    assert not hasattr(project, "TokenInterface")
    atexit.register(_cleanup)


def _cleanup():
    for path in ("build", "reports"):
        path = Path('tests/brownie-test-project').joinpath(path)
        if path.exists():
            shutil.rmtree(str(path))
