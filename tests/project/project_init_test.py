#!/usr/bin/python3

import pytest

from brownie import project
from brownie.exceptions import ProjectAlreadyLoaded


def test_check_for_project():
    path = project.check_for_project('tests/brownie-test-project')
    assert path == project.check_for_project('tests/brownie-test-project/contracts')
    assert not project.check_for_project('/')


def test_load_already_loaded():
    with pytest.raises(ProjectAlreadyLoaded):
        project.load('tests/brownie-test-project')
