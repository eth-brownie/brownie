#!/usr/bin/python3

import sys

import pytest

from brownie._cli import run as cli_run


def test_run_no_args_lists_scripts(testproject, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["brownie", "run"])
    with pytest.raises(SystemExit):
        cli_run.main()
    out = capsys.readouterr().out
    assert "Available scripts in path scripts:" in out
    assert "token" in out
    assert "main" in out
