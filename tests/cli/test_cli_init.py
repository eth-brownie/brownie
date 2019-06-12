#!/usr/bin/python3

import os
from pathlib import Path
import pytest
import sys

from brownie import config
from brownie.cli.init import main as init_main


@pytest.fixture(autouse=True, scope="module")
def setup():
    argv = sys.argv
    sys.argv = ['brownie', 'init']
    yield
    sys.argv = argv


def test_init_project(testpath, noload):
    init_main()
    project_path = Path(testpath)
    for path in ("contracts", "scripts", "reports", "tests", "brownie-config.json"):
        assert project_path.joinpath(path).exists()


def test_init_inside(testpath, noload):
    init_main()
    os.chdir(testpath+"/contracts")
    config['folders']['project'] = False
    with pytest.raises(SystemError):
        init_main()
    assert not Path(testpath).joinpath("contracts/brownie-config.json").exists()
