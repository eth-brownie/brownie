#!/usr/bin/python3

from collections import deque
import pytest

from brownie.cli.console import Console
from brownie import accounts, history, rpc, project
import brownie

cmd = deque([])


@pytest.fixture(scope="function")
def console(monkeypatch):
    brownie.a = accounts
    brownie.Token = project.Token
    brownie.__all__.extend(['a', 'Token'])
    rpc.reset()
    cmd.clear()
    monkeypatch.setattr('builtins.input', _input)
    monkeypatch.setattr('brownie.cli.utils.color.format_tb', _raise)
    yield Console()
    del brownie.a
    del brownie.Token
    brownie.__all__.remove('a')
    brownie.__all__.remove('Token')


def _input(x):
    if not cmd:
        return "exit()"
    return cmd.popleft()


def _raise(exc, start):
    raise exc[0](exc[1])


def test_simple(console):
    balance = accounts[1].balance()
    cmd.append('accounts[0].transfer(accounts[1], "1 ether")')
    console._run()
    assert len(history) == 1
    assert accounts[1].balance() == balance + 1000000000000000000


def test_run(console):
    cmd.append('run("token")')
    console._run()
    assert len(history) == 1
    assert len(project.Token) == 1


def test_multiple_commands(console):
    cmd.extend('''dir()
accounts[0].deploy(Token, "", "", 18, 100000000)
Token[0].transfer(a[1], 10000)
'''.split('\n'))
    console._run()
    assert len(history) == 2
    assert project.Token[0].balanceOf(accounts[1]) == 10000


def test_multiline_commands(console):
    cmd.extend('''to_send = [

(1, "1 ether"),
(2, "5 ether"),
(3, "7 ether"),
]
for i in to_send:
    a[0].transfer(a[i[0]], i[1])
'''.split('\n'))
    console._run()
    assert len(history) == 3
    assert accounts[1].balance() == 101000000000000000000
    assert accounts[2].balance() == 105000000000000000000
    assert accounts[3].balance() == 107000000000000000000


def test_fn(console):
    cmd.extend('''
def x():
    a[0].transfer(a[1], "1 ether")
    a[0].transfer(a[1], "2 ether")

x()'''.split('\n'))
    console._run()
    assert len(history) == 2
    assert accounts[1].balance() == 103000000000000000000


def test_exceptions(console):
    cmd.append('x += 22')
    with pytest.raises(NameError):
        console._run()
    cmd.append('x = 1 + "hello"')
    with pytest.raises(TypeError):
        console._run()
    cmd.extend(['x=[]', 'x[11] = "hello"'])
    with pytest.raises(IndexError):
        console._run()


def test_syntax(console):
    cmd.append('x = [)')
    with pytest.raises(SyntaxError):
        console._run()
    cmd.extend(['x = [', '', ')'])
    with pytest.raises(SyntaxError):
        console._run()
