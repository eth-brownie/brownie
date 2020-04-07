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


def test_list_no_installed(capfd):
    cli_pm._list()
    assert "No packages are currently installed." in capfd.readouterr()[0]


def test_list_installed(capfd):
    _mk_repo_path("testorg", "testrepo@1.0.0")
    _mk_repo_path("testorg", "testrepo@1.0.1")

    cli_pm._list()
    stdout = capfd.readouterr()[0]
    assert "1.0.0" in stdout
    assert "1.0.1" in stdout


def test_list_remove_spurious_files(capfd):
    bad_path1 = _mk_repo_path("emptynothing")
    bad_path2 = _mk_repo_path("bad-repo", "package-without-version")
    with bad_path2.parent.joinpath("package-as-file@1.0.0").open("w") as fp:
        fp.write("i'm a file!")

    cli_pm._list()
    assert "No packages are currently installed." in capfd.readouterr()[0]
    assert not bad_path1.exists()
    assert not bad_path2.exists()


def test_clone(tmp_path):
    _mk_repo_path("testorg", "testrepo@1.0.0")
    cli_pm._clone("testorg/testrepo@1.0.0", tmp_path.as_posix())

    assert tmp_path.joinpath("testorg").exists()


def test_clone_not_installed(tmp_path):
    with pytest.raises(FileNotFoundError):
        cli_pm._clone("testorg/testrepo@1.0.0", tmp_path.as_posix())


def test_clone_already_exists(tmp_path):
    _mk_repo_path("testorg", "testrepo@1.0.0")
    cli_pm._clone("testorg/testrepo@1.0.0", tmp_path.as_posix())

    with pytest.raises(FileExistsError):
        cli_pm._clone("testorg/testrepo@1.0.0", tmp_path.as_posix())


def test_delete(tmp_path):
    path = _mk_repo_path("testorg", "testrepo@1.0.0")
    cli_pm._delete("testorg/testrepo@1.0.0")

    assert not path.exists()


def test_delete_not_installed(tmp_path):
    with pytest.raises(FileNotFoundError):
        cli_pm._delete("testorg/testrepo@1.0.0")
