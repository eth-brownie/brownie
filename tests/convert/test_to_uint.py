#!/usr/bin/python3

import pytest

from brownie.convert import to_uint


def test_success():
    assert to_uint(123) == 123
    assert to_uint("1 ether") == 1000000000000000000
    assert to_uint("0xFF") == 255


def test_overflow():
    for i in range(8, 264, 8):
        type_ = "uint" + str(i)
        assert to_uint(2**i - 1, type_) == 2**i - 1
        with pytest.raises(OverflowError):
            to_uint(2**i, type_)


def test_overflow_uint():
    assert to_uint(2**256 - 1) == 2**256 - 1
    with pytest.raises(OverflowError):
        to_uint(2**256)
    assert to_uint(2**256 - 1, "uint") == 2**256 - 1
    with pytest.raises(OverflowError):
        to_uint(2**256, "uint")


def test_underflow():
    assert to_uint("0") == 0
    with pytest.raises(OverflowError):
        to_uint(-1)


def test_type():
    for i in range(8, 264, 8):
        assert to_uint(0, "uint" + str(i)) == 0
        with pytest.raises(ValueError):
            to_uint(0, "uint" + str(i - 1))
