#!/usr/bin/python3

import sys

import pytest
from prompt_toolkit.input.defaults import create_pipe_input

from brownie._cli.console import Console

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="stdin pipe issues")


@pytest.fixture
def console(testproject, monkeypatch):
    monkeypatch.setattr("brownie._cli.console.Console.showtraceback", _exception)
    monkeypatch.setattr("brownie._cli.console.Console.showsyntaxerror", _exception)
    argv = sys.argv
    sys.argv = ["brownie", "console"]
    c = Console(testproject, create_pipe_input())
    yield c
    sys.argv = argv


def _run_cmd(console, cmd):
    for line in cmd:
        console.push(line)


def _exception(obj, *args):
    obj.resetbuffer()
    raise sys.exc_info()[0]


def test_simple(console, accounts, history):
    balance = accounts[1].balance()
    _run_cmd(console, ['accounts[0].transfer(accounts[1], "1 ether")'])
    assert len(history) == 1
    assert accounts[1].balance() == balance + 1000000000000000000


def test_run(BrownieTester, history, console):
    _run_cmd(console, ['run("token")'])
    assert len(history) == 1
    assert len(BrownieTester) == 1


def test_multiple_commands(BrownieTester, accounts, history, console):
    _run_cmd(
        console,
        [
            "config",
            "accounts[0].deploy(BrownieTester, True)",
            "BrownieTester[0].doNothing()",
            'accounts.add("0x416b8a7d9290502f5661da81f0cf43893e3d19cb9aea3c426cfb36e8186e9c09")',
        ],
    )
    assert len(history) == 2
    assert BrownieTester[0].owner() == accounts[0]


def test_multiline_commands(accounts, history, console):
    _run_cmd(
        console,
        [
            "to_send = [",
            '(1, "1 ether"),',
            '(2, "5 ether"),',
            '(3, "7 ether"),',
            "]",
            "to_send",
            "for i in to_send:",
            "    accounts[0].transfer(accounts[i[0]], i[1])",
            "",
        ],
    )
    assert len(history) == 3
    assert accounts[1].balance() == "101 ether"
    assert accounts[2].balance() == "105 ether"
    assert accounts[3].balance() == "107 ether"


def test_fn(accounts, history, console):
    _run_cmd(
        console,
        [
            "def x():",
            '    accounts[0].transfer(accounts[1], "1 ether")',
            '    accounts[0].transfer(accounts[1], "2 ether")',
            "",
            "x()",
        ],
    )
    assert len(history) == 2
    assert accounts[1].balance() == "103 ether"


def test_exceptions(console):
    with pytest.raises(NameError):
        console.push("x += 22")
    with pytest.raises(TypeError):
        console.push('x = 1 + "hello"')
    with pytest.raises(IndexError):
        _run_cmd(console, ["x=[]", 'x[11] = "hello"'])


def test_syntax(console):
    with pytest.raises(SyntaxError):
        console.push("x = [)")
    with pytest.raises(SyntaxError):
        _run_cmd(console, ["x = [", "", ")"])


def test_dir(console):
    _run_cmd(console, ["dir()", "dir(network)", "dir(accounts)", "dir(project)", "dir(alert)"])
