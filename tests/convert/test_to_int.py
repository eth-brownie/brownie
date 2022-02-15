#!/usr/bin/python3

import pytest

from brownie.convert import to_int


def test_success():
    assert to_int(123) == 123
    assert to_int("1 ether") == 1000000000000000000
    assert to_int(-1984) == -1984


def test_overflow():
    for i in range(8, 264, 8):
        type_ = "int" + str(i)
        assert to_int((2**i // 2) - 1, type_) == (2**i // 2) - 1
        with pytest.raises(OverflowError):
            to_int(2**i // 2, type_)


def test_overflow_uint():
    assert to_int((2**256 // 2) - 1) == (2**256 // 2) - 1
    with pytest.raises(OverflowError):
        to_int(2**256 // 2)
    assert to_int((2**256 // 2) - 1, "int") == (2**256 // 2) - 1
    with pytest.raises(OverflowError):
        to_int(2**256 // 2, "int")


def test_underflow():
    for i in range(8, 264, 8):
        type_ = "int" + str(i)
        assert to_int((-(2**i) // 2), type_) == (-(2**i) // 2)
        with pytest.raises(OverflowError):
            to_int(-(2**i) // 2 - 1, type_)


def test_type():
    for i in range(8, 264, 8):
        assert to_int(0, "int" + str(i)) == 0
        with pytest.raises(ValueError):
            to_int(0, "int" + str(i - 1))
