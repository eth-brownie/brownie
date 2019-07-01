#!/usr/bin/python3

import os
import pytest
import sys

from brownie.cli.utils.console import Console
from brownie import accounts, history, project, rpc


@pytest.fixture(scope="function")
def console():
    argv = sys.argv
    sys.argv = ['brownie', 'console']
    original_path = os.getcwd()
    os.chdir(original_path+"/tests/brownie-test-project")
    rpc.snapshot()
    c = Console()
    c.push('from brownie.project import *')
    yield c
    rpc.revert()
    os.chdir(original_path)
    sys.argv = argv


def _run_cmd(console, cmd):
    for line in cmd:
        console.push(line)


def _exception(obj, *args):
    obj.resetbuffer()
    raise sys.exc_info()[0]


def test_simple(console):
    balance = accounts[1].balance()
    _run_cmd(console, ['accounts[0].transfer(accounts[1], "1 ether")'])
    assert len(history) == 1
    assert accounts[1].balance() == balance + 1000000000000000000


def test_run(console):
    _run_cmd(console, ['run("token")'])
    assert len(history) == 1
    assert len(project.Token) == 1


def test_multiple_commands(console):
    _run_cmd(console, [
        'dir()',
        'accounts[0].deploy(Token, "", "", 18, 100000000)',
        'Token[0].transfer(accounts[1], 10000, {"from": accounts[0]})',
        'accounts.add("0x416b8a7d9290502f5661da81f0cf43893e3d19cb9aea3c426cfb36e8186e9c09")'
    ])
    assert len(history) == 2
    assert project.Token[0].balanceOf(accounts[1]) == 10000


def test_multiline_commands(console):
    _run_cmd(console, [
        'to_send = [',
        '(1, "1 ether"),',
        '(2, "5 ether"),',
        '(3, "7 ether"),',
        ']',
        'for i in to_send:',
        '    accounts[0].transfer(accounts[i[0]], i[1])',
        ''
    ])
    assert len(history) == 3
    assert accounts[1].balance() == 101000000000000000000
    assert accounts[2].balance() == 105000000000000000000
    assert accounts[3].balance() == 107000000000000000000


def test_fn(console):
    _run_cmd(console, [
        'def x():',
        '    accounts[0].transfer(accounts[1], "1 ether")',
        '    accounts[0].transfer(accounts[1], "2 ether")',
        '',
        'x()'
    ])
    assert len(history) == 2
    assert accounts[1].balance() == 103000000000000000000


def test_exceptions(console, monkeypatch):
    monkeypatch.setattr('brownie.cli.utils.console.Console.showtraceback', _exception)
    with pytest.raises(NameError):
        console.push('x += 22')
    with pytest.raises(TypeError):
        console.push('x = 1 + "hello"')
    with pytest.raises(IndexError):
        _run_cmd(console, ['x=[]', 'x[11] = "hello"'])


def test_syntax(console, monkeypatch):
    monkeypatch.setattr('brownie.cli.utils.console.Console.showsyntaxerror', _exception)
    with pytest.raises(SyntaxError):
        console.push('x = [)')
    with pytest.raises(SyntaxError):
        _run_cmd(console, ['x = [', '', ')'])
