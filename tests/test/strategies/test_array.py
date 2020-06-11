#!/usr/bin/python3

import pytest
from hypothesis import given
from hypothesis.strategies import SearchStrategy

from brownie.test import strategy


@pytest.mark.parametrize(
    "type_str", ["address", "bool", "bytes32", "decimal", "int", "string", "uint"]
)
def test_strategy(type_str):
    assert isinstance(strategy(f"{type_str}[2]"), SearchStrategy)
    assert isinstance(strategy(f"{type_str}[]"), SearchStrategy)
    assert isinstance(strategy(f"{type_str}[][2]"), SearchStrategy)
    assert isinstance(strategy(f"{type_str}[2][]"), SearchStrategy)


def test_size_typeerror():
    with pytest.raises(TypeError):
        strategy("uint8[]", min_length=(1,))
    with pytest.raises(TypeError):
        strategy("uint8[]", max_length=(4,))


def test_size_wrong_length():
    with pytest.raises(ValueError):
        strategy("uint8[][2][]", min_length=[1, 2, 3])
    with pytest.raises(ValueError):
        strategy("uint8[][2][]", min_length=[1])


@given(value=strategy("uint8[2][5]"))
def test_given(value):
    assert isinstance(value, list)
    assert len(value) == 5
    for item in value:
        assert isinstance(item, list)
        assert len(item) == 2
        assert isinstance(item[0], int)
        assert 0 <= item[0] <= 255


@given(value=strategy("uint8[][]", min_length=2))
def test_min_int(value):
    assert isinstance(value, list)
    assert 2 <= len(value) <= 8
    for item in value:
        assert isinstance(item, list)
        assert 2 <= len(item) <= 8
        assert isinstance(item[0], int)
        assert 0 <= item[0] <= 255


@given(value=strategy("uint8[][]", min_length=[4, 3]))
def test_min_list(value):
    assert isinstance(value, list)
    assert 3 <= len(value) <= 8
    for item in value:
        assert isinstance(item, list)
        assert 4 <= len(item) <= 8
        assert isinstance(item[0], int)
        assert 0 <= item[0] <= 255


@given(value=strategy("uint8[][]", max_length=4))
def test_max_int(value):
    assert isinstance(value, list)
    assert 1 <= len(value) <= 4
    for item in value:
        assert isinstance(item, list)
        assert 1 <= len(item) <= 4
        assert isinstance(item[0], int)
        assert 0 <= item[0] <= 255


@given(value=strategy("uint8[][]", max_length=[2, 4]))
def test_max_list(value):
    assert isinstance(value, list)
    assert 1 <= len(value) <= 4
    for item in value:
        assert isinstance(item, list)
        assert 1 <= len(item) <= 2
        assert isinstance(item[0], int)
        assert 0 <= item[0] <= 255


@given(value=strategy("uint8[2]", min_value=12, max_value=42, exclude=23))
def test_kwargs_passthrough(value):
    assert len(value) == 2
    assert 12 <= value[0] <= 42
    assert 12 <= value[1] <= 42
    assert 23 not in value
