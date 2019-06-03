#!/usr/bin/python3

from pathlib import Path
import pytest

from brownie import project, config
from brownie.project import sources
from brownie.exceptions import ProjectAlreadyLoaded, ProjectNotFound


def test_namespace():
    assert hasattr(project, 'Token'), "did not initialize Token ContractContainer"
    assert hasattr(project, 'SafeMath'), "did not initialize SafeMath ContractContainer"
    assert not hasattr(project, "TokenABC"), "initialized TokenABC ContractContainer"
    assert not hasattr(project, "TokenInterface"), "initialized TokenInterface ContractContainer"


def test_check_for_project():
    path = project.check_for_project('tests/brownie-test-project')
    assert path == project.check_for_project('tests/brownie-test-project/contracts')
    assert not project.check_for_project('/')


def test_new(noload, tmpdir):
    assert tmpdir == project.new(tmpdir)
    assert config['folders']['project'] == tmpdir
    assert Path(tmpdir).joinpath('brownie-config.json').exists()


def test_new_raises(noload, tmpdir):
    project.new(tmpdir)
    with pytest.raises(ProjectAlreadyLoaded):
        project.new(tmpdir)
    project.close()
    with pytest.raises(SystemError):
        project.new(tmpdir+"/contracts")


def test_load_raises_already_loaded():
    with pytest.raises(ProjectAlreadyLoaded):
        project.load('tests/brownie-test-project')


def test_load_raises_cannot_find(noload, tmpdir):
    with pytest.raises(ProjectNotFound):
        project.load(tmpdir)


def test_close():
    project.close()
    project.close(False)
    with pytest.raises(ProjectNotFound):
        project.close()
    project.load('tests/brownie-test-project')


def test_compile():
    source = sources.get('BrownieTester')
    source = source.replace('BrownieTester', 'TempTester')
    source = source.replace('UnlinkedLib', 'TestLib')
    obj = project.compile_source(source)
    assert obj[0]._name == "TempTester"
    assert obj[1]._name == "TestLib"


def test_create_folders(tmpdir):
    project.main._create_folders(Path(tmpdir))
    for path in ("contracts", "scripts", "reports", "tests", "build"):
        assert Path(tmpdir).joinpath(path).exists()
