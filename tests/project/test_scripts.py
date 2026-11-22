#!/usr/bin/python3

import pytest

from brownie.project.scripts import _get_scripts_tree, run


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
    with pytest.raises(FileNotFoundError) as excinfo:
        run("scripts/foo")
    assert "Available scripts" in str(excinfo.value)
    assert "token" in str(excinfo.value)
    assert "main" in str(excinfo.value)
    with pytest.raises(FileNotFoundError):
        run("/foo")


def test_no_method(testproject):
    with pytest.raises(AttributeError) as excinfo:
        run("token", method_name="foo")
    assert "has no method 'foo'" in str(excinfo.value)
    assert "Available methods: args_method, do_nothing, kwargs_method, main" in str(excinfo.value)
    for method in ("main", "args_method", "kwargs_method", "do_nothing"):
        assert method in str(excinfo.value)


def test_no_method_excludes_private(testproject):
    with testproject._path.joinpath("scripts/other.py").open("w") as fp:
        fp.write("def _hidden():\n    pass\n\n\ndef visible():\n    return 1\n")
    with pytest.raises(AttributeError) as excinfo:
        run("other", method_name="foo")
    assert "Available methods: visible" in str(excinfo.value)
    assert "_hidden" not in str(excinfo.value)


def test_scripts_tree(tmp_path):
    scripts = tmp_path.joinpath("scripts")
    sub = scripts.joinpath("sub")
    sub.mkdir(parents=True)
    scripts.joinpath("token.py").write_text("def _hidden():\n    pass\n\n\ndef main():\n    pass\n")
    scripts.joinpath("broken.py").write_text("def broken(:\n")
    scripts.joinpath("notes.txt").write_text("not a script")
    sub.joinpath("deploy.py").write_text("def deploy():\n    pass\n")
    tree = _get_scripts_tree(scripts)
    assert "token" in tree
    assert "main" in tree
    assert "_hidden" not in tree
    assert "broken" in tree
    assert "sub" in tree
    assert "deploy" in tree
    assert "notes" not in tree


def test_scripts_tree_rebinding(tmp_path):
    scripts = tmp_path.joinpath("scripts")
    scripts.mkdir(parents=True)
    scripts.joinpath("deploy.py").write_text(
        "def _deploy():\n    pass\n\n\ndef main():\n    pass\n\n\nasync def fetch():\n    pass\n\n\nmain = None\ndeploy = _deploy\nlaunch = deploy\nhandler = lambda: None\nrun_handler = handler\nstale = main\n"
    )
    scripts.joinpath("cleanup.py").write_text("def temp():\n    pass\n\n\ndel temp\n")
    tree = _get_scripts_tree(scripts)
    assert "deploy" in tree
    assert "launch" in tree
    assert "fetch" in tree
    assert "handler" in tree
    assert "run_handler" in tree
    assert "main" not in tree
    assert "stale" not in tree
    assert "_deploy" not in tree
    assert "temp" not in tree


def test_no_script_lists_all_projects(testproject, otherproject):
    with testproject._path.joinpath("scripts/only_testproject.py").open("w") as fp:
        fp.write("def main(): pass\n")
    with otherproject._path.joinpath("scripts/only_other.py").open("w") as fp:
        fp.write("def main(): pass\n")
    with pytest.raises(FileNotFoundError) as excinfo:
        run("scripts/foo")
    assert "only_testproject" in str(excinfo.value)
    assert "only_other" in str(excinfo.value)


def test_no_script_absolute_lists_matching_project(testproject, otherproject):
    with testproject._path.joinpath("scripts/only_testproject.py").open("w") as fp:
        fp.write("def main(): pass\n")
    with otherproject._path.joinpath("scripts/only_other.py").open("w") as fp:
        fp.write("def main(): pass\n")
    missing = otherproject._path.joinpath("scripts/missing.py")
    with pytest.raises(FileNotFoundError) as excinfo:
        run(missing.as_posix())
    assert "only_other" in str(excinfo.value)
    assert "only_testproject" not in str(excinfo.value)
