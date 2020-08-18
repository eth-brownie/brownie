#!/usr/bin/python3

import pytest

from brownie.project.scripts import run


def test_run(BrownieTester):
    run("token")
    assert len(BrownieTester) == 1


def test_args(testproject):
    assert run("token", method_name="args_method", args=("foo",)) == "foo"


def test_kwargs(testproject):
    kwargs = {"first": "foo", "second": "bar"}
    assert run("token", method_name="kwargs_method", kwargs=kwargs) == ("foo", "bar")


def test_paths(testproject, devnetwork):
    run("token")
    run("token.py")
    run(testproject._path.joinpath("scripts/token").as_posix())


def test_reload(testproject):
    assert run("token", method_name="do_nothing") == "potato"
    with testproject._path.joinpath("scripts/token.py").open("a") as fp:
        fp.write("\ndef new_method(): return 42\n")
    assert run("token", method_name="new_method") == 42


def test_multiple_projects(testproject, otherproject):
    assert testproject._path != otherproject._path
    with otherproject._path.joinpath("scripts/other.py").open("w") as fp:
        fp.write("def main(): return 42")
    assert run("other") == 42
    otherproject.close()
    with pytest.raises(FileNotFoundError):
        run("other")


def test_no_script(testproject):
    with pytest.raises(FileNotFoundError):
        run("scripts/foo")
    with pytest.raises(FileNotFoundError):
        run("/foo")


def test_no_method(testproject):
    with pytest.raises(AttributeError):
        run("token", method_name="foo")
