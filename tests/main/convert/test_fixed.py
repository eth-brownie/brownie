#!/usr/bin/python3

from decimal import Decimal

import pytest

from brownie.convert import Fixed


def test_nonetype():
    with pytest.raises(TypeError):
        Fixed(None)


def test_bytes():
    assert Fixed(b"\xff") == 255


def test_scientific_notation():
    assert Fixed("8.32e26") == 832000000000000000000000000


def test_float():
    with pytest.raises(TypeError):
        Fixed(1.99)


def test_int():
    assert Fixed(1000) == 1000


def test_str():
    assert Fixed("1000.123456789123456789") == Decimal("1000.123456789123456789")


def test_hexstr():
    assert Fixed("0xff") == 255


def test_string_with_unit():
    assert Fixed("3.66 ether") == 3660000000000000000
    assert Fixed("89.006 gwei") == 89006000000


def test_type():
    assert type(Fixed(12)) is Fixed


def test_eq():
    assert Fixed("1") == 1
    assert not Fixed("123") == "obviously not a number"
    with pytest.raises(TypeError):
        Fixed("1.0") == 1.0


def test_ne():
    assert Fixed("1") != 2
    assert Fixed("123") != "obviously not a number"
    with pytest.raises(TypeError):
        Fixed("1.0") != 1.1


def test_lt():
    assert Fixed("1 ether") < "2 ether"
    with pytest.raises(TypeError):
        Fixed("1.0") < 1.1


def test_le():
    assert Fixed("1 ether") <= "2 ether"
    assert Fixed("1 ether") <= "1 ether"
    with pytest.raises(TypeError):
        Fixed("1.0") <= 1.1


def test_gt():
    assert Fixed("2 ether") > "1 ether"
    with pytest.raises(TypeError):
        Fixed("2.0") > 1.0


def test_ge():
    assert Fixed("2 ether") >= "1 ether"
    assert Fixed("2 ether") >= "2 ether"
    with pytest.raises(TypeError):
        Fixed("2.0") >= 2.0
