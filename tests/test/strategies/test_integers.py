#!/usr/bin/python3

import pytest
from hypothesis import given
from hypothesis.strategies import SearchStrategy

from brownie.test import strategy


@pytest.mark.parametrize("bits", range(8, 257, 8))
def test_strategy(bits):
    type_str = f"uint{bits}"
    assert isinstance(strategy(type_str), SearchStrategy)

    type_str = f"int{bits}"
    assert isinstance(strategy(type_str), SearchStrategy)


@pytest.mark.parametrize("type_str", ["int", "uint"])
def test_invalid_bits(type_str):
    with pytest.raises(ValueError):
        strategy(f"{type_str}1")
    with pytest.raises(ValueError):
        strategy(f"{type_str}264")
    with pytest.raises(ValueError):
        strategy(f"{type_str}69")


def test_invalid_min_max():
    # min too low
    with pytest.raises(ValueError):
        strategy("uint", min_value=-1)
    with pytest.raises(ValueError):
        strategy("int", min_value=-(2**255) - 1)

    # max too high
    with pytest.raises(ValueError):
        strategy("uint", max_value=2**256)

    # min > max
    with pytest.raises(ValueError):
        strategy("int", min_value=42, max_value=12)
    with pytest.raises(ValueError):
        strategy("uint8", min_value=1024)
    with pytest.raises(ValueError):
        strategy("int8", max_value=-129)


@given(value=strategy("uint"))
def test_uint_given(value):
    assert type(value) is int
    assert 0 <= value <= 2**256 - 1


@given(value=strategy("uint8"))
def test_uint8_given(value):
    assert type(value) is int
    assert 0 <= value <= 255


@given(value=strategy("int"))
def test_int_given(value):
    assert -(2**255) <= value <= 2**255 - 1


@given(value=strategy("int8"))
def test_int8_given(value):
    assert -128 <= value <= 127


@given(value=strategy("int8", min_value=-12, max_value=42))
def test_int_min_max(value):
    assert -12 <= value <= 42


@given(value=strategy("uint8", min_value=12, max_value=42))
def test_uint_min_max(value):
    assert 12 <= value <= 42


@given(value=strategy("uint8", exclude=[4, 8, 15, 16, 23, 42]))
def test_exclude(value):
    assert value not in [4, 8, 15, 16, 23, 42]


def test_exclude_repr():
    st = strategy("uint8", exclude=42)
    assert repr(st) == "integers(min_value=0, max_value=255, exclude=(42,))"
