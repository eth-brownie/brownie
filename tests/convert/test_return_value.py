#!/usr/bin/python3

import pytest

from brownie.convert.datatypes import EthAddress, HexString, ReturnValue, Wei
from brownie.project import compile_source

string_fixture = "bar baz"


@pytest.fixture
def return_value(accounts, tester):
    yield tester.manyValues(
        88, [False, False, False], accounts[2], [("0x1234", "0x6666")], string_fixture
    )


def test_type(return_value):
    assert isinstance(return_value, ReturnValue)
    assert isinstance(return_value["_addr"], EthAddress)
    assert isinstance(return_value["_bool"], ReturnValue)
    assert isinstance(return_value["_bool"][0], bool)
    assert isinstance(return_value["_num"], Wei)
    assert isinstance(return_value["_bytes"], ReturnValue)
    assert isinstance(return_value["_bytes"][0][0], HexString)


def test_len(return_value):
    assert len(return_value) == 5


def test_count(return_value):
    assert return_value.count(2) == 0
    assert return_value.count([("0x1234", "0x6666")]) == 1


def test_index(return_value):
    assert return_value.index([("0x1234", "0x6666")]) == 3
    assert return_value.index([("0x1234", "0x6666")], 1, 4) == 3
    with pytest.raises(ValueError):
        return_value.index([("0x1234", "0x6666")], stop=2)
    with pytest.raises(ValueError):
        return_value.index("foo")


def test_contains_conversions(accounts, return_value):
    assert 88 in return_value
    assert "88 wei" in return_value
    assert False in return_value[1]
    assert True not in return_value[1]
    assert 0 not in return_value[1]
    assert accounts[2] in return_value
    assert str(accounts[2]) in return_value
    assert accounts[1] not in return_value
    assert "0x1234" in return_value[3][0]
    assert "0x00001234" in return_value[3][0]


def test_eq_conversions(accounts, return_value):
    data = [88, [False, False, False], accounts[2], [("0x1234", "0x6666")], string_fixture]
    assert return_value == data
    assert return_value == tuple(data)
    data[1] = tuple(data[1])
    data[3] = tuple(data[3])
    assert return_value == tuple(data)


def test_ne_conversions(accounts, return_value):
    data = [88, [False, False, False], accounts[2], [("0x1234", "0x6666")], string_fixture]
    assert not return_value != data
    assert not return_value != tuple(data)
    data[1] = tuple(data[1])
    data[3] = tuple(data[3])
    assert not return_value != tuple(data)


def test_dict(accounts, return_value):
    d = return_value.dict()
    assert isinstance(d, dict)
    assert len(d) == 5
    assert len(d["_bool"]) == 3
    assert sorted(d) == ["_addr", "_bool", "_bytes", "_num", "_string"]
    assert d["_addr"] == accounts[2]


def test_keys(return_value):
    assert list(return_value.keys()) == ["_num", "_bool", "_addr", "_bytes", "_string"]


def test_items(return_value):
    assert return_value.items() == return_value.dict().items()


def test_getitem(accounts, return_value):
    assert return_value[2] == return_value["_addr"] == accounts[2]
    assert return_value[0] == return_value["_num"] == 88


def test_getitem_slice(accounts, return_value):
    s = return_value[1:3]
    assert s == [[False, False, False], accounts[2]]
    assert isinstance(s, ReturnValue)
    assert s[0] == s["_bool"]
    assert "_num" not in s


def test_ethaddress_typeerror():
    e = EthAddress("0x0063046686E46Dc6F15918b61AE2B121458534a5")
    with pytest.raises(TypeError):
        e == "potato"
    with pytest.raises(TypeError):
        e == "0x00"
    assert str(e) != "potato"


def test_hexstring_typeerror():
    b = HexString("0x1234", "bytes32")
    with pytest.raises(TypeError):
        b == "potato"
    with pytest.raises(TypeError):
        b == "1234"
    assert str(b) != "potato"


def test_hexstring_length():
    b = HexString("0x1234", "bytes32")
    assert b == "0x1234"
    assert b == "0x000000000000001234"


def test_hashable():
    assert hash(ReturnValue([1, 2])) == hash(tuple([1, 2]))
    assert set(ReturnValue([3, 1, 3, 3, 7])) == set([3, 1, 3, 3, 7])


def test_decimals(vypertester):
    ret = vypertester.fixedType("1.234", ["-42", "3.1337"])
    assert ret == ["1.234", "-42", "3.1337"]


def test_dynamic_tuple_array(accounts):
    code = """
pragma solidity ^0.6.0;
pragma experimental ABIEncoderV2;

contract Test {

struct Foo { uint256 a; }

Foo[] bar;

function foo() public returns (Foo[] memory a) {
    bar.push(Foo(1));
    bar.push(Foo(6));
    return bar;
}

}
"""
    contract = compile_source(code).Test.deploy({"from": accounts[0]})

    assert contract.foo.call() == [(1,), (6,)]


def test_fixed_tuple_array(accounts):
    code = """
pragma solidity ^0.6.0;
pragma experimental ABIEncoderV2;

contract Test {

struct Foo { uint256 a; string b; }

Foo[2][2] bar;

function foo() public returns (Foo[2][2] memory, Foo[2] memory) {
    bar[0][0].a = 42;
    bar[0][0].b = "hello";
    bar[1][1].a = 69;
    return (bar, bar[1]);
}

}
"""
    contract = compile_source(code).Test.deploy({"from": accounts[0]})

    assert contract.foo.call() == [
        ([(42, "hello"), (0, "")], [(0, ""), (69, "")]),
        [(0, ""), (69, "")],
    ]
