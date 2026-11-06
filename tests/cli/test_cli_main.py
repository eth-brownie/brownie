#!/usr/bin/python3

import sys
from io import BytesIO
from zipfile import ZipFile

import pytest
from requests import Response

from brownie import project
from brownie._cli import __main__ as cli_main


@pytest.fixture
def cli_tester(monkeypatch, mocker, argv, config, project):
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
        return

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


def test_cli_init(cli_tester, tmp_path):
    cli_tester.monkeypatch.setattr(sys, "argv", ["brownie", "init"])
    cli_main.main()
    assert tmp_path.joinpath("contracts").is_dir()
    assert tmp_path.joinpath(".gitignore").is_file()

    target = tmp_path.joinpath("test/path")
    target.mkdir(parents=True)
    marker = target.joinpath("existing.txt")
    marker.write_text("keep")
    cli_tester.monkeypatch.setattr(sys, "argv", ["brownie", "init", str(target)])
    with pytest.raises(SystemExit, match="Directory is not empty"):
        cli_main.main()
    cli_tester.monkeypatch.setattr(sys, "argv", ["brownie", "init", str(target), "--force"])
    cli_main.main()
    assert target.joinpath("contracts").is_dir()
    assert marker.read_text() == "keep"


def test_cli_bake(cli_tester, tmp_path):
    source = "contract Token {}\n"
    archive = BytesIO()
    with ZipFile(archive, "w") as mix:
        mix.writestr("token-mix-main/contracts/Token.sol", source)

    responses = {
        "https://api.github.com/repos/brownie-mix/token-mix": b'{"default_branch": "main"}',
        "https://github.com/brownie-mix/token-mix/archive/main.zip": archive.getvalue(),
    }

    def get_response(url, **kwargs):
        response = Response()
        response.status_code = 200
        response.raw = BytesIO(responses[url])
        response.headers["content-length"] = str(len(responses[url]))
        return response

    cli_tester.monkeypatch.setattr("requests.get", get_response)
    cli_tester.monkeypatch.setattr(sys, "argv", ["brownie", "bake", "token"])
    cli_main.main()
    assert tmp_path.joinpath("token/contracts/Token.sol").read_text() == source

    target = tmp_path.joinpath("test/path")
    cli_tester.monkeypatch.setattr(
        sys, "argv", ["brownie", "bake", "token", str(target), "--force"]
    )
    cli_main.main()
    assert target.joinpath("contracts/Token.sol").read_text() == source


def test_cli_compile(cli_tester, testproject, capfd):
    project_path = testproject._path
    testproject.close()
    for args in (["brownie", "compile"], ["brownie", "compile", "--all"]):
        cli_tester.monkeypatch.setattr(sys, "argv", args)
        cli_main.main()
        assert "Project has been compiled." in capfd.readouterr().out
        artifacts = project_path.joinpath("build/contracts")
        assert artifacts.joinpath("BrownieTester.json").is_file()
        for loaded in project.get_loaded_projects():
            loaded.close()


def test_cli_compile_and_analyze_projectnotfound_exception(cli_tester):
    cli_tester.monkeypatch.setattr("brownie.project.load", cli_tester.mock_subroutines)

    with pytest.raises(SystemExit):
        cli_tester.run_and_test_parameters("compile", parameters=None)
    with pytest.raises(SystemExit):
        cli_tester.run_and_test_parameters("analyze", parameters=None)

    assert cli_tester.mock_subroutines.called is False
    assert cli_tester.mock_subroutines.call_count == 0


def test_cli_run_with_missing_file(cli_tester):
    cli_tester.monkeypatch.setattr("brownie.run", cli_tester.mock_subroutines)

    subtargets = ("brownie.network.connect",)
    for target in subtargets:
        cli_tester.monkeypatch.setattr(target, cli_tester.mock_subroutines)

    with pytest.raises(SystemExit):
        cli_tester.run_and_test_parameters("run testfile", parameters=None)

    assert cli_tester.mock_subroutines.called is True
    assert cli_tester.mock_subroutines.call_count == 1


def test_cli_run_with_raise_flag(cli_tester):
    cli_tester.monkeypatch.setattr("brownie.run", cli_tester.mock_subroutines)

    subtargets = ("brownie.network.connect",)
    for target in subtargets:
        cli_tester.monkeypatch.setattr(target, cli_tester.mock_subroutines)

    with pytest.raises(FileNotFoundError):
        cli_tester.run_and_test_parameters("run testfile -r", parameters=None)

    assert cli_tester.mock_subroutines.called is True
    assert cli_tester.mock_subroutines.call_count == 1


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


def test_cli_console_doesnt_accept_compile(cli_tester):
    with pytest.raises(SystemExit):
        cli_tester.run_and_test_parameters("console --compile")


def test_cli_console_accepts_no_compile(cli_tester):
    cli_tester.monkeypatch.setattr("brownie._cli.console.main", cli_tester.mock_subroutines)

    cli_tester.run_and_test_parameters("console")
    cli_tester.run_and_test_parameters("console --no-compile")

    assert cli_tester.mock_subroutines.called is True
    assert cli_tester.mock_subroutines.call_count == 2
