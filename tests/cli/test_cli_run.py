#!/usr/bin/python3

import sys

import pytest

from brownie._cli import run as cli_run


def test_run_no_args_lists_scripts(testproject, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["brownie", "run"])
    with pytest.raises(SystemExit) as excinfo:
        cli_run.main()
    out = capsys.readouterr().out
    assert "Available scripts in path scripts:" in out
    assert "token" in out
    assert "main" in out
    assert "Usage: brownie run <filename>" in str(excinfo.value.code)


def test_run_no_args_from_subdirectory_lists_scripts(testproject, monkeypatch, capsys):
    monkeypatch.chdir(testproject._path.joinpath("scripts"))
    monkeypatch.setattr(sys, "argv", ["brownie", "run"])
    with pytest.raises(SystemExit) as excinfo:
        cli_run.main()
    out = capsys.readouterr().out
    assert "Available scripts in path" in out
    assert "token" in out
    assert "Usage: brownie run <filename>" in str(excinfo.value.code)


def test_run_help(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["brownie", "run", "--help"])
    with pytest.raises(SystemExit) as excinfo:
        cli_run.main()
    assert excinfo.value.code in (0, None)
    out = capsys.readouterr().out
    assert "Usage: brownie run <filename>" in out
    assert "Available scripts" not in out
