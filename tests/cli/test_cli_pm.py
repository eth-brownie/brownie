#!/usr/bin/python3

import shutil

import pytest

from brownie._cli import pm as cli_pm
from brownie._config import _get_data_folder


@pytest.fixture(autouse=True)
def setup():
    yield
    path = _get_data_folder().joinpath("packages")
    shutil.rmtree(path)
    path.mkdir()


def _mk_repo_path(*folder_names):
    path = _get_data_folder().joinpath("packages")

    for name in folder_names:
        path = path.joinpath(name)
        path.mkdir(exist_ok=True)

    return path


def test_list_no_installed(runner):
    result = runner.invoke(cli_pm.list)
    assert "No packages are currently installed." in result.output


def test_list_installed(runner):
    _mk_repo_path("testorg", "testrepo@1.0.0")
    _mk_repo_path("testorg", "testrepo@1.0.1")

    result = runner.invoke(cli_pm.list)
    assert "1.0.0" in result.output
    assert "1.0.1" in result.output


def test_list_remove_spurious_files(runner):
    bad_path1 = _mk_repo_path("emptynothing")
    bad_path2 = _mk_repo_path("bad-repo", "package-without-version")
    with bad_path2.parent.joinpath("package-as-file@1.0.0").open("w") as fp:
        fp.write("i'm a file!")

    result = runner.invoke(cli_pm.list)
    assert "No packages are currently installed." in result.output
    assert not bad_path1.exists()
    assert not bad_path2.exists()


def test_clone(tmp_path, runner):
    _mk_repo_path("testorg", "testrepo@1.0.0")
    runner.invoke(cli_pm.clone, ["testorg/testrepo@1.0.0", tmp_path.as_posix()])

    assert tmp_path.joinpath("testorg").exists()


def test_clone_not_installed(tmp_path, runner):
    result = runner.invoke(cli_pm.clone, ["testorg/testrepo@1.0.0", tmp_path.as_posix()])
    assert isinstance(result.exception, FileNotFoundError) is True


def test_clone_already_exists(tmp_path, runner):
    _mk_repo_path("testorg", "testrepo@1.0.0")
    runner.invoke(cli_pm.clone, ["testorg/testrepo@1.0.0", tmp_path.as_posix()])

    result = runner.invoke(cli_pm.clone, ["testorg/testrepo@1.0.0", tmp_path.as_posix()])
    assert isinstance(result.exception, FileExistsError) is True


def test_delete(tmp_path, runner):
    path = _mk_repo_path("testorg", "testrepo@1.0.0")
    runner.invoke(cli_pm.delete, ["testorg/testrepo@1.0.0"])

    assert not path.exists()


def test_delete_not_installed(tmp_path, runner):
    result = runner.invoke(cli_pm.delete, ["testorg/testrepo@1.0.0"])
    assert isinstance(result.exception, FileNotFoundError) is True
