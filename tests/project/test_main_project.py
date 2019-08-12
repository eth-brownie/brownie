#!/usr/bin/python3

from pathlib import Path
import pytest

from brownie.exceptions import ProjectAlreadyLoaded, ProjectNotFound


def test_namespace(project, testproject):
    assert hasattr(project, 'TestProject')
    assert hasattr(testproject, 'BrownieTester')
    assert hasattr(testproject, 'SafeMath')
    assert not hasattr(testproject, "TokenABC")
    assert not hasattr(testproject, "TokenInterface")


def test_check_for_project(project, testproject):
    path = project.check_for_project(testproject._project_path)
    assert path == project.check_for_project(testproject._project_path.joinpath('contracts'))
    assert not project.check_for_project('/')


def test_new(tmp_path, project):
    assert str(tmp_path) == project.new(tmp_path)
    assert tmp_path.joinpath('brownie-config.json').exists()


def test_pull(project, tmp_path):
    path = project.pull('token')
    assert path != tmp_path
    assert Path(path).joinpath('brownie-config.json').exists()
    assert Path(path).joinpath('contracts/Token.sol').exists()
    assert Path(path).joinpath('contracts/SafeMath.sol').exists()
    project.load(path)


def test_pull_raises(project, tmp_path):
    project.new(tmp_path.joinpath('token'))
    with pytest.raises(FileExistsError):
        project.pull('token')
    with pytest.raises(SystemError):
        project.pull(tmp_path.joinpath("token/contracts"))


def test_load_raises_already_loaded(project, testproject):
    with pytest.raises(ProjectAlreadyLoaded):
        project.load(testproject._project_path, 'TestProject')


def test_load_raises_cannot_find(project, tmp_path):
    with pytest.raises(ProjectNotFound):
        project.load(tmp_path)


def test_close(testproject):
    testproject.close()
    testproject.close(False)
    with pytest.raises(ProjectNotFound):
        testproject.close()


def test_compile(project, solc5source):
    obj = project.compile_source(solc5source)
    assert 'Foo' in obj
    assert 'Bar' in obj


def test_create_folders(project, tmp_path):
    project.main._create_folders(Path(tmp_path))
    for path in ("contracts", "scripts", "reports", "tests", "build"):
        assert Path(tmp_path).joinpath(path).exists()
