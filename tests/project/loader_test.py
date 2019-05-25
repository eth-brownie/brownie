#!/usr/bin/python3

import pytest

from brownie import project
from brownie.project import loader
from brownie.exceptions import ProjectAlreadyLoaded, ProjectNotFound


def test_check_for_project():
    path = loader.check_for_project('tests/brownie-test-project')
    assert path == loader.check_for_project('tests/brownie-test-project/contracts')
    assert not loader.check_for_project('/')


def test_load_already_loaded():
    with pytest.raises(ProjectAlreadyLoaded):
        loader.load('tests/brownie-test-project')


def test_close():
    loader.close()
    loader.close(False)
    with pytest.raises(ProjectNotFound):
        loader.close()
    loader.load('tests/brownie-test-project')


def test_contract_containers():
    assert hasattr(project, 'Token'), "did not initialize Token ContractContainer"
    assert hasattr(project, 'SafeMath'), "did not initialize SafeMath ContractContainer"
    assert not hasattr(project, "TokenABC"), "initialized TokenABC ContractContainer"
    assert not hasattr(project, "TokenInterface"), "initialized TokenInterface ContractContainer"
