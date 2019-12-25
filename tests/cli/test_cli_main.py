#!/usr/bin/python3

import sys

import pytest

from brownie._cli.__main__ import main as cli_main
from brownie._cli.console import Console as cli_console


@pytest.fixture
def cli_tester(monkeypatch, mocker):
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

    def run_and_test_parameters(self, argv, parameters={}):
        sys.argv = ["brownie"] + argv.split(" ")
        cli_main()
        assert self.mock_subroutines.call_args == parameters

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


def test_cli_analyze(cli_tester, testproject):
    cli_tester.monkeypatch.setattr("brownie.project.load", cli_tester.mock_subroutines)
    cli_tester.run_and_test_parameters("analyze")

    assert cli_tester.mock_subroutines.called is True
    assert cli_tester.mock_subroutines.call_count == 1


def test_cli_console(cli_tester, testproject):
    testproject.close()
    console = cli_console(testproject)

    cli_tester.monkeypatch.setattr(
        "brownie._cli.console.Console.interact", cli_tester.mock_subroutines
    )
    cli_tester.monkeypatch.setattr("brownie._cli.console.Console", lambda console_object: console)

    subtargets = ("brownie.network.connect",)
    for target in subtargets:
        cli_tester.monkeypatch.setattr(target, cli_tester.mock_subroutines)

    args = (console,)
    kwargs = {"banner": "Brownie environment is ready.", "exitmsg": ""}
    parameters = (args, kwargs)
    cli_tester.run_and_test_parameters("console", parameters)

    assert cli_tester.mock_subroutines.called is True
    assert cli_tester.mock_subroutines.call_count == (len(subtargets) + 1)


# travis doesn't like this

# def test_cli_gui(cli_tester, project_path):
#     cli_tester.patch('brownie.gui.Gui.mainloop')
#     cli_tester.counter_patch('brownie.project.load')
#     cli_tester('gui')


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


def test_cli_incorrect(cli_tester):
    with pytest.raises(SystemExit):
        cli_tester.run_and_test_parameters("foo")
