#!/usr/bin/python3

import sys

import pytest

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="stdin pipe issues")


def _run_cmd(console, cmd):
    for line in cmd:
        console.push(line)


def test_simple(console, accounts, history):
    shell = console()
    balance = accounts[1].balance()
    _run_cmd(shell, ['accounts[0].transfer(accounts[1], "1 ether")'])
    assert len(history) == 1
    assert accounts[1].balance() == balance + 1000000000000000000


def test_run(testproject, history, console, accounts):
    shell = console(testproject)
    _run_cmd(shell, ['run("token")'])
    assert len(history) == 1
    assert len(testproject.BrownieTester) == 1


def test_multiple_commands(testproject, accounts, history, console):
    shell = console(testproject)
    _run_cmd(
        shell,
        [
            "config",
            "accounts[0].deploy(BrownieTester, True)",
            "BrownieTester[0].doNothing()",
            'accounts.add("0x416b8a7d9290502f5661da81f0cf43893e3d19cb9aea3c426cfb36e8186e9c09")',
        ],
    )
    assert len(history) == 2
    assert testproject.BrownieTester[0].owner() == accounts[0]


def test_multiple_commands_with_nocompile(testproject_nocompile, accounts, history, console):
    shell = console(testproject_nocompile)
    _run_cmd(
        shell,
        [
            "config",
            "accounts[0].deploy(BrownieTester, True)",
            "BrownieTester[0].doNothing()",
            'accounts.add("0x416b8a7d9290502f5661da81f0cf43893e3d19cb9aea3c426cfb36e8186e9c09")',
        ],
    )
    assert len(history) == 2
    assert testproject_nocompile.BrownieTester[0].owner() == accounts[0]


def test_multiline_commands(accounts, history, console):
    shell = console()
    _run_cmd(
        shell,
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
    assert accounts[1].balance() == "1001 ether"
    assert accounts[2].balance() == "1005 ether"
    assert accounts[3].balance() == "1007 ether"


def test_fn(accounts, history, console):
    shell = console()
    _run_cmd(
        shell,
        [
            "def x():",
            '    accounts[0].transfer(accounts[1], "1 ether")',
            '    accounts[0].transfer(accounts[1], "2 ether")',
            "",
            "x()",
        ],
    )
    assert len(history) == 2
    assert accounts[1].balance() == "1003 ether"


def test_exceptions(console):
    shell = console()
    with pytest.raises(NameError):
        shell.push("x += 22")
    with pytest.raises(TypeError):
        shell.push('x = 1 + "hello"')
    with pytest.raises(IndexError):
        _run_cmd(shell, ["x=[]", 'x[11] = "hello"'])


def test_syntax(console):
    shell = console()
    with pytest.raises(SyntaxError):
        shell.push("x = [)")
    with pytest.raises(SyntaxError):
        _run_cmd(shell, ["x = [", "", ")"])


def test_dir(console):
    shell = console()
    _run_cmd(shell, ["dir()", "dir(network)", "dir(accounts)", "dir(project)", "dir(alert)"])


def test_exit_and_open_new_console(console):
    shell = console()
    with pytest.raises(SystemExit):
        shell.push("exit()")
    shell = console()
    shell.push("foo = 1")
