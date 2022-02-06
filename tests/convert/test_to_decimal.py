#!/usr/bin/python3

from decimal import Decimal

import pytest

from brownie.convert import Fixed, to_decimal


def test_return_type():
    assert isinstance(to_decimal(123), Decimal)
    assert type(to_decimal(123)) is Fixed


def test_success():
    assert to_decimal(123) == 123
    assert to_decimal("-3.1337") == Decimal("-3.1337")
    assert to_decimal("1 ether") == 1000000000000000000
    assert to_decimal(Decimal(42)) == 42
    assert to_decimal(Fixed(6)) == "6"


def test_incorrect_type():
    with pytest.raises(TypeError, match="Cannot convert float to decimal - use a string instead"):
        to_decimal(3.1337)
    with pytest.raises(TypeError):
        to_decimal(None)


def test_bounds():
    to_decimal(-(2**127))
    with pytest.raises(OverflowError):
        to_decimal(-(2**127) - 1)
    to_decimal(2**127 - 1)
    with pytest.raises(OverflowError):
        to_decimal(2**127)


def test_decimal_points():
    to_decimal("1.0000000001")
    to_decimal("1.00000000010000000")
    with pytest.raises(ValueError):
        to_decimal("1.00000000001")
