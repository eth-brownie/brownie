#!/usr/bin/python3

import sys
from pathlib import Path

import pytest

from brownie.exceptions import ProjectAlreadyLoaded, ProjectNotFound
from brownie.project.main import Project, TempProject, _ProjectBase


def test_object(testproject):
    assert type(testproject) is Project
    assert isinstance(testproject, _ProjectBase)


def test_namespace(project, testproject):
    assert hasattr(project, "TestProject")
    assert hasattr(testproject, "BrownieTester")
    assert hasattr(testproject, "SafeMath")
    assert not hasattr(testproject, "TokenABC")
    assert not hasattr(testproject, "TokenInterface")
    assert "brownie.project.TestProject" in sys.modules
    testproject.close()
    assert not hasattr(project, "TestProject")
    assert "brownie.project.TestProject" not in sys.modules


def test_check_for_project(project, testproject):
    path = project.check_for_project(testproject._project_path)
    assert path == project.check_for_project(testproject._project_path.joinpath("contracts"))
    assert not project.check_for_project("/")


def test_new(tmp_path, project):
    assert str(tmp_path) == project.new(tmp_path)
    assert tmp_path.joinpath("brownie-config.json").exists()


def test_from_brownie_mix_raises(project, tmp_path):
    project.new(tmp_path.joinpath("token"))
    with pytest.raises(FileExistsError):
        project.from_brownie_mix("token")
    with pytest.raises(SystemError):
        project.from_brownie_mix(tmp_path.joinpath("token/contracts"))


def test_load_raises_already_loaded(project, testproject):
    with pytest.raises(ProjectAlreadyLoaded):
        project.load(testproject._project_path, "TestProject")
    with pytest.raises(ProjectAlreadyLoaded):
        testproject.load()


def test_load_raises_cannot_find(project, tmp_path):
    with pytest.raises(ProjectNotFound):
        project.load(tmp_path)


def test_reload_from_project_object(project, testproject):
    assert hasattr(project, "TestProject")
    assert len(project.get_loaded_projects()) == 1
    testproject.close()
    assert not hasattr(project, "TestProject")
    assert len(project.get_loaded_projects()) == 0
    testproject.load()
    assert hasattr(project, "TestProject")
    assert len(project.get_loaded_projects()) == 1


def test_load_multiple(project, testproject):
    other = project.load(testproject._project_path, "OtherProject")
    assert hasattr(project, "OtherProject")
    assert len(project.get_loaded_projects()) == 2
    other.close()
    assert not hasattr(project, "OtherProject")
    assert hasattr(project, "TestProject")
    assert len(project.get_loaded_projects()) == 1


def test_close(project, testproject):
    testproject.close()
    assert len(project.get_loaded_projects()) == 0
    testproject.close(False)
    with pytest.raises(ProjectNotFound):
        testproject.close()


def test_compile_object(project, solc5source):
    temp = project.compile_source(solc5source)
    assert type(temp) is TempProject
    assert isinstance(temp, _ProjectBase)
    assert len(temp) == 2
    assert "Foo" in temp
    assert "Bar" in temp


def test_compile_namespace(project, solc5source):
    project.compile_source(solc5source)
    assert not hasattr(project, "TempProject")
    assert "brownie.project.TempProject" not in sys.modules
    assert len(project.get_loaded_projects()) == 0


def test_compile_multiple(project, solc5source):
    a = project.compile_source(solc5source)
    b = project.compile_source(solc5source)
    assert a != b


def test_create_folders(project, tmp_path):
    project.main._create_folders(Path(tmp_path))
    for path in ("contracts", "scripts", "reports", "tests", "build"):
        assert Path(tmp_path).joinpath(path).exists()
