#!/usr/bin/python3

from brownie._cli import analyze as cli_analyze
from brownie._cli import bake as cli_bake
from brownie._cli import compile as cli_compile
from brownie._cli import init as cli_init
from brownie._cli import run as cli_run
from brownie._cli import test as cli_test
from brownie.exceptions import ProjectNotFound


def test_cli_init(mocker, runner):
    mocked_new = mocker.patch("brownie.project.new")

    result = runner.invoke(cli_init.cli)
    assert result.exception is None
    assert "SUCCESS" in result.output

    result = runner.invoke(cli_init.cli, ["--path", "test/path", "--force"])
    assert result.exception is None
    assert "SUCCESS" in result.output

    assert mocked_new.call_count == 2


def test_cli_bake(mocker, runner):
    mocked_bake = mocker.patch("brownie.project.from_brownie_mix")

    result = runner.invoke(cli_bake.cli, ["token"])
    assert result.exception is None
    assert "SUCCESS" in result.output

    path = "test/path"
    result = runner.invoke(cli_bake.cli, ["token", "--path", path, "--force"])
    assert result.exception is None
    assert "SUCCESS" in result.output

    assert mocked_bake.call_count == 2


def test_cli_compile(runner, testproject, mocker):
    mocked_load = mocker.patch("brownie.project.load")

    result = runner.invoke(cli_compile.cli)
    assert not result.exception
    assert "Project has been compiled." in result.output

    runner.invoke(cli_compile.cli, ["--all"])
    assert not result.exception
    assert "Project has been compiled." in result.output

    assert mocked_load.call_count == 2


def test_cli_compile_and_analyze_projectnotfound_exception(mocker, monkeypatch, runner):
    mocked_load = mocker.patch("brownie.project.load")

    result = runner.invoke(cli_compile.cli)
    assert isinstance(result.exception, ProjectNotFound) is True

    monkeypatch.setenv("MYTHX_API_KEY", "foo")
    result = runner.invoke(cli_analyze.cli)
    assert isinstance(result.exception, ProjectNotFound) is True

    assert mocked_load.call_count == 0


def test_cli_run_with_missing_file(mocker, runner):
    mocked_run = mocker.patch("brownie.run")
    mocked_connect = mocker.patch("brownie.network.connect")

    result = runner.invoke(cli_run.cli, ["testfile"])
    assert isinstance(result.exception, FileNotFoundError) is True

    assert mocked_run.call_count == 0
    assert mocked_connect.call_count == 1


# def test_cli_ethpm(cli_tester, testproject):
#     cli_tester.monkeypatch.setattr("brownie._cli.ethpm._list", cli_tester.mock_subroutines)
#
#     args = (testproject._path,)
#     kwargs = {}
#     parameters = (args, kwargs)
#     cli_tester.run_and_test_parameters("ethpm list", parameters)
#     cli_tester.run_and_test_parameters("ethpm foo", parameters)
#
#     assert cli_tester.mock_subroutines.called is True
#     assert cli_tester.mock_subroutines.call_count == 1


# def test_cli_ethpm_with_projectnotfound_exception(cli_tester):
#     cli_tester.monkeypatch.setattr("brownie._cli.ethpm._list", cli_tester.mock_subroutines)
#
#     with pytest.raises(SystemExit):
#         cli_tester.run_and_test_parameters("ethpm list", parameters=None)
#
#     assert cli_tester.mock_subroutines.called is False
#     assert cli_tester.mock_subroutines.call_count == 0
#
#
# def test_cli_ethpm_with_type_error_exception(cli_tester, testproject):
#     cli_tester.monkeypatch.setattr(
#         "brownie._cli.ethpm._list",
#         lambda project_path: cli_tester.raise_type_error_exception("foobar"),
#     )
#
#     cli_tester.run_and_test_parameters("ethpm list", parameters=None)
#
#     assert cli_tester.mock_subroutines.called is False
#     assert cli_tester.mock_subroutines.call_count == 0


def test_test_no_args(mocker, testproject, runner):
    mocked_test = mocker.patch("pytest.main")
    runner.invoke(cli_test.cli)
    assert mocked_test.call_count == 1


def test_test_args(mocker, testproject, runner):
    mocked_test = mocker.patch("pytest.main")
    runner.invoke(cli_test.cli, ["tests/test_foo.py", "--gas", "-n", "1"])
    # TODO: Verify that arguments work
    assert mocked_test.call_count == 1


# def test_cli_incorrect(cli_tester):
#     with pytest.raises(SystemExit):
#         cli_tester.run_and_test_parameters("foo")
#
#
# def test_levenshtein(cli_tester):
#     with pytest.raises(SystemExit, match="Did you mean 'brownie accounts'"):
#         cli_tester.run_and_test_parameters("account")


# def test_no_args_shows_help(cli_tester, capfd):
#     with pytest.raises(SystemExit):
#         cli_tester.run_and_test_parameters()
#     assert cli_main.__doc__ in capfd.readouterr()[0].strip()


# def test_cli_pm(cli_tester):
#     cli_tester.run_and_test_parameters("pm list", None)
