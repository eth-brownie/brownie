#!/usr/bin/python3

import sys
from pathlib import Path

import pytest

from brownie.exceptions import ProjectAlreadyLoaded, ProjectNotFound
from brownie.project.main import Project, TempProject, _ProjectBase


def test_object(newproject):
    assert type(newproject) is Project
    assert isinstance(newproject, _ProjectBase)


def test_namespace(project, testproject):
    assert hasattr(project, "TestProject")
    assert hasattr(testproject, "BrownieTester")
    assert hasattr(testproject, "SafeMath")
    assert "brownie.project.TestProject" in sys.modules
    testproject.close()
    assert not hasattr(project, "TestProject")
    assert "brownie.project.TestProject" not in sys.modules


def test_check_for_project(project, newproject):
    path = project.check_for_project(newproject._path)
    assert path == project.check_for_project(newproject._path.joinpath("contracts"))
    assert not project.check_for_project("/")


def test_new(tmp_path, project):
    assert str(tmp_path) == project.new(tmp_path)
    assert tmp_path.joinpath("brownie-config.yaml").exists()
    assert tmp_path.joinpath("ethpm-config.yaml").exists()
    assert tmp_path.joinpath(".gitattributes").exists()
    assert tmp_path.joinpath(".gitignore").exists()


def test_load_raises_already_loaded(project, newproject):
    newproject.load()
    with pytest.raises(ProjectAlreadyLoaded):
        project.load(newproject._path, "NewProject")
    with pytest.raises(ProjectAlreadyLoaded):
        newproject.load()


def test_load_raises_cannot_find(project, tmp_path):
    with pytest.raises(ProjectNotFound):
        project.load(tmp_path)


def test_reload_from_project_object(project, newproject):
    assert not hasattr(project, "NewProject")
    assert len(project.get_loaded_projects()) == 0
    newproject.load()
    assert hasattr(project, "NewProject")
    assert len(project.get_loaded_projects()) == 1
    newproject.close()
    assert not hasattr(project, "NewProject")
    assert len(project.get_loaded_projects()) == 0
    newproject.load()
    assert hasattr(project, "NewProject")
    assert len(project.get_loaded_projects()) == 1


def test_load_multiple(project, newproject):
    newproject.load()
    other = project.load(newproject._path, "OtherProject")
    assert hasattr(project, "OtherProject")
    assert len(project.get_loaded_projects()) == 2
    other.close()
    assert not hasattr(project, "OtherProject")
    assert hasattr(project, "NewProject")
    assert len(project.get_loaded_projects()) == 1


def test_close(project, newproject):
    assert len(project.get_loaded_projects()) == 0
    newproject.load()
    assert len(project.get_loaded_projects()) == 1
    newproject.close()
    assert len(project.get_loaded_projects()) == 0
    newproject.close(False)
    with pytest.raises(ProjectNotFound):
        newproject.close()


def test_compile_solc_object(project, solc5source):
    temp = project.compile_source(solc5source)
    assert type(temp) is TempProject
    assert isinstance(temp, _ProjectBase)
    assert len(temp) == 2
    assert temp._name == "TempSolcProject"
    assert "Foo" in temp
    assert "Bar" in temp


def test_compile_vyper_object(project):
    temp = project.compile_source("@public\ndef x() -> bool: return True")
    assert type(temp) is TempProject
    assert isinstance(temp, _ProjectBase)
    assert len(temp) == 1
    assert temp._name == "TempVyperProject"
    assert "Vyper" in temp


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
    for path in ("contracts", "interfaces", "scripts", "reports", "tests", "build"):
        assert Path(tmp_path).joinpath(path).exists()


def test_from_ethpm(ipfs_mock, project):
    p = project.from_ethpm("ipfs://testipfs-math")
    assert type(p) is TempProject
    assert "Math" in p
    assert not len(p.Math)


def test_from_ethpm_with_deployments(ipfs_mock, project, network):
    network.connect("mainnet")
    p = project.from_ethpm("ipfs://testipfs-math")
    assert len(p.Math) == 1
    assert p.Math[0].address == "0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2"
