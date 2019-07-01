#!/usr/bin/python3

import pytest

from brownie import network, project, accounts


def test_get_method():
    assert project.Token.get_method(
        "0xa9059cbb0000000000000000000000000a4a71b2518f7a3273595cba15c3308182b32cd1"
        "0000000000000000000000000000000000000000000000020f5b1eaad8d80000"
    ) == "transfer"


def test_container(clean_network):
    Token = project.Token
    assert len(Token) == 0
    t = Token.deploy("", "", 0, 0, {'from': accounts[0]})
    t2 = Token.deploy("", "", 0, 0, {'from': accounts[0]})
    assert len(Token) == 2
    assert Token[0] == t
    assert Token[1] == t2
    assert list(Token) == [t, t2]
    assert t in Token
    del Token[0]
    assert len(Token) == 1
    assert Token[0] == t2
    network.rpc.reset()
    assert len(Token) == 0


def test_remove_at(clean_network):
    Token = project.Token
    t = Token.deploy("", "", 0, 0, {'from': accounts[0]})
    Token.remove(t)
    assert len(Token) == 0
    assert Token.at(t.address) == t
    assert len(Token) == 1
    t2 = Token.deploy("", "", 0, 0, {'from': accounts[0]})
    t2._name = "Potato"
    with pytest.raises(TypeError):
        Token.remove(t2)
    with pytest.raises(TypeError):
        Token.remove(123)
