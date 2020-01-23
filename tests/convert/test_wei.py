#!/usr/bin/python3

from brownie.convert import Wei


def test_nonetype():
    assert Wei(None) == 0


def test_bytes():
    assert Wei(b"\xff") == 255


def test_scientific_notation():
    assert Wei(8.32e26) == 832000000000000000000000000


def test_float():
    assert Wei(1.99) == 1


def test_int():
    assert Wei(1000) == 1000


def test_str():
    assert Wei("1000") == 1000


def test_hexstr():
    assert Wei("0xff") == 255


def test_string_with_unit():
    assert Wei("3.66 ether") == 3660000000000000000
    assert Wei("89.006 gwei") == 89006000000


def test_type():
    assert type(Wei(12)) is Wei


def test_eq():
    assert Wei("1 ether") == "1 ether"


def test_ne():
    assert Wei("1 ether") != "2 ether"


def test_lt():
    assert Wei("1 ether") < "2 ether"


def test_le():
    assert Wei("1 ether") <= "2 ether"
    assert Wei("1 ether") <= "1 ether"


def test_gt():
    assert Wei("2 ether") > "1 ether"


def test_ge():
    assert Wei("2 ether") >= "1 ether"
    assert Wei("2 ether") >= "2 ether"
