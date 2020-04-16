#!/usr/bin/python3

import sys

import pytest

from brownie._cli import __main__ as cli_main


@pytest.fixture
def cli_tester(monkeypatch, mocker, argv, config):
    tester = CliTester(monkeypatch, mocker)
    tester.mocker.spy(tester, "mock_subroutines")

    yield tester
    tester.close()


class CliTester:
    def __init__(self, monkeypatch, mocker):
        self.argv = sys.argv.copy()
        self.monkeypatch = monkeypatch
        self.mocker = mocker

    def mock_subroutines(self, *args, **kwargs):
        return True

    def run_and_test_parameters(self, argv=None, parameters={}):
        sys.argv = ["brownie"]
        if argv:
            sys.argv += argv.split(" ")
        cli_main.main()
        assert self.mock_subroutines.call_args == parameters

    def raise_type_error_exception(self, e):
        raise TypeError(e)

    def close(self):
        sys.argv = self.argv


def test_cli_init(cli_tester):
    cli_tester.monkeypatch.setattr("brownie.project.new", cli_tester.mock_subroutines)

    args = (".", False)
    kwargs = {}
    parameters = (args, kwargs)
    cli_tester.run_and_test_parameters("init", parameters)

    args = ("test/path", True)
    parameters = (args, kwargs)
    cli_tester.run_and_test_parameters("init test/path --force", parameters)

    assert cli_tester.mock_subroutines.called is True
    assert cli_tester.mock_subroutines.call_count == 2


def test_cli_bake(cli_tester):
    cli_tester.monkeypatch.setattr("brownie.project.from_brownie_mix", cli_tester.mock_subroutines)

    args = ("token", None, False)
    kwargs = {}
    parameters = (args, kwargs)
    cli_tester.run_and_test_parameters("bake token", parameters)

    args = ("token", "test/path", True)
    parameters = (args, kwargs)
    cli_tester.run_and_test_parameters("bake token test/path --force", parameters)

    assert cli_tester.mock_subroutines.called is True
    assert cli_tester.mock_subroutines.call_count == 2


def test_cli_compile(cli_tester, testproject):
    cli_tester.monkeypatch.setattr("brownie.project.load", cli_tester.mock_subroutines)

    args = (testproject._path,)
    kwargs = {}
    parameters = (args, kwargs)
    cli_tester.run_and_test_parameters("compile", parameters)
    cli_tester.run_and_test_parameters("compile --all", parameters)

    assert cli_tester.mock_subroutines.called is True
    assert cli_tester.mock_subroutines.call_count == 2


def test_cli_analyze_with_mocked_project(cli_tester, testproject):
    cli_tester.monkeypatch.setattr("brownie.project.load", cli_tester.mock_subroutines)
    cli_tester.run_and_test_parameters("analyze")

    assert cli_tester.mock_subroutines.called is True
    assert cli_tester.mock_subroutines.call_count == 1


def test_cli_compile_and_analyze_projectnotfound_exception(cli_tester):
    cli_tester.monkeypatch.setattr("brownie.project.load", cli_tester.mock_subroutines)

    cli_tester.run_and_test_parameters("compile", parameters=None)
    cli_tester.run_and_test_parameters("analyze", parameters=None)

    assert cli_tester.mock_subroutines.called is False
    assert cli_tester.mock_subroutines.call_count == 0


def test_cli_run(cli_tester, testproject):
    cli_tester.monkeypatch.setattr("brownie.run", cli_tester.mock_subroutines)

    subtargets = ("brownie.network.connect",)
    for target in subtargets:
        cli_tester.monkeypatch.setattr(target, cli_tester.mock_subroutines)

    args = ("testfile",)
    kwargs = {"method_name": "main"}
    parameters = (args, kwargs)
    cli_tester.run_and_test_parameters("run testfile", parameters)

    assert cli_tester.mock_subroutines.called is True
    assert cli_tester.mock_subroutines.call_count == (len(subtargets) + 1)


def test_cli_run_with_projectnotfound_exception(cli_tester):
    cli_tester.monkeypatch.setattr("brownie.run", cli_tester.mock_subroutines)

    subtargets = ("brownie.network.connect",)
    for target in subtargets:
        cli_tester.monkeypatch.setattr(target, cli_tester.mock_subroutines)

    cli_tester.run_and_test_parameters("run testfile", parameters=None)

    assert cli_tester.mock_subroutines.called is False
    assert cli_tester.mock_subroutines.call_count == 0


def test_cli_ethpm(cli_tester, testproject):
    cli_tester.monkeypatch.setattr("brownie._cli.ethpm._list", cli_tester.mock_subroutines)

    args = (testproject._path,)
    kwargs = {}
    parameters = (args, kwargs)
    cli_tester.run_and_test_parameters("ethpm list", parameters)
    cli_tester.run_and_test_parameters("ethpm foo", parameters)

    assert cli_tester.mock_subroutines.called is True
    assert cli_tester.mock_subroutines.call_count == 1


def test_cli_ethpm_with_projectnotfound_exception(cli_tester):
    cli_tester.monkeypatch.setattr("brownie._cli.ethpm._list", cli_tester.mock_subroutines)

    cli_tester.run_and_test_parameters("ethpm list", parameters=None)

    assert cli_tester.mock_subroutines.called is False
    assert cli_tester.mock_subroutines.call_count == 0


def test_cli_ethpm_with_type_error_exception(cli_tester, testproject):
    cli_tester.monkeypatch.setattr(
        "brownie._cli.ethpm._list",
        lambda project_path: cli_tester.raise_type_error_exception("foobar"),
    )

    cli_tester.run_and_test_parameters("ethpm list", parameters=None)

    assert cli_tester.mock_subroutines.called is False
    assert cli_tester.mock_subroutines.call_count == 0


def test_test_no_args(cli_tester, testproject):
    cli_tester.monkeypatch.setattr("pytest.main", cli_tester.mock_subroutines)
    params = ([testproject._path.joinpath("tests").as_posix()], ["pytest-brownie"])
    cli_tester.run_and_test_parameters("test", (params, {}))

    assert cli_tester.mock_subroutines.called is True
    assert cli_tester.mock_subroutines.call_count == 1


def test_test_args(cli_tester, testproject):
    cli_tester.monkeypatch.setattr("pytest.main", cli_tester.mock_subroutines)
    params = (["tests/test_foo.py", "--gas", "-n", "1"], ["pytest-brownie"])
    cli_tester.run_and_test_parameters("test tests/test_foo.py --gas -n 1", (params, {}))

    assert cli_tester.mock_subroutines.called is True
    assert cli_tester.mock_subroutines.call_count == 1


def test_cli_incorrect(cli_tester):
    with pytest.raises(SystemExit):
        cli_tester.run_and_test_parameters("foo")


def test_levenshtein(cli_tester):
    with pytest.raises(SystemExit, match="Did you mean 'brownie accounts'"):
        cli_tester.run_and_test_parameters("account")


def test_no_args_shows_help(cli_tester, capfd):
    with pytest.raises(SystemExit):
        cli_tester.run_and_test_parameters()
    assert cli_main.__doc__ in capfd.readouterr()[0].strip()


def test_cli_pm(cli_tester):
    cli_tester.run_and_test_parameters("pm list", None)
