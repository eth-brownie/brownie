#!/usr/bin/python3

import pytest

from brownie import accounts
from brownie.convert import ReturnValue, EthAddress, HexString, Wei


@pytest.fixture(scope="module")
def ret(tester):
    yield tester.returnMultiple(88, False, accounts[2], "0x1234")


def test_type(ret):
    assert type(ret) is ReturnValue
    assert type(ret['_addr']) is EthAddress
    assert type(ret['_bool']) is bool
    assert type(ret['_num']) is Wei
    assert type(ret['_bytes']) is HexString


def test_len(ret):
    assert len(ret) == 4


def test_count(ret):
    assert ret.count(2) == 0
    assert ret.count("0x1234") == 1


def test_index(ret):
    assert ret.index('0x1234') == 3
    assert ret.index('0x1234', 1, 4) == 3
    with pytest.raises(ValueError):
        ret.index('0x1234', stop=2)
    with pytest.raises(ValueError):
        ret.index("foo")


def test_contains_conversions(ret):
    assert 88 in ret
    assert "88 wei" in ret
    assert False in ret
    assert True not in ret
    assert 0 not in ret
    assert accounts[2] in ret
    assert str(accounts[2]) in ret
    assert accounts[1] not in ret
    assert "0x1234" in ret
    assert "0x00001234" in ret


def test_eq_conversions(ret):
    assert ret == (88, False, accounts[2], "0x1234")
    assert ret == [88, False, accounts[2], "0x1234"]
    assert ret == ["88 wei", False, str(accounts[2]), "0x000001234"]


def test_dict(ret):
    d = ret.dict()
    assert type(d) is dict
    assert len(d) == 4
    assert sorted(d) == ['_addr', '_bool', '_bytes', '_num']
    assert d['_bool'] is False
    assert d['_addr'] == accounts[2]


def test_keys(ret):
    assert list(ret.keys()) == ['_num', '_bool', '_addr', '_bytes']


def test_items(ret):
    assert ret.items() == ret.dict().items()


def test_getitem(ret):
    assert ret[2] == ret['_addr'] == accounts[2]
    assert ret[0] == ret['_num'] == 88


def test_getitem_slice(ret):
    s = ret[1:3]
    assert s == [False, accounts[2]]
    assert s == (False, accounts[2])
    assert type(s) is ReturnValue
    assert s[0] == s['_bool']
    assert '_num' not in s


def test_ethaddress_typeerror(ret):
    e = ret[2]
    with pytest.raises(TypeError):
        e == "potato"
    with pytest.raises(TypeError):
        e == "0x00"
    assert str(e) != "potato"


def test_hexstring_typeerror(ret):
    b = ret[3]
    with pytest.raises(TypeError):
        b == "potato"
    with pytest.raises(TypeError):
        b == "1234"
    assert str(b) != "potato"


def test_hexstring_length(ret):
    b = ret[3]
    assert b == "0x1234"
    assert b == "0x000000000000001234"
