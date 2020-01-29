#!/usr/bin/python3

import pytest
from hypothesis import given
from hypothesis.strategies import SearchStrategy

from brownie.test import strategy


def test_strategy():
    assert isinstance(strategy("byte"), SearchStrategy)
    assert isinstance(strategy("bytes"), SearchStrategy)
    assert isinstance(strategy("bytes32"), SearchStrategy)


def test_invalid_bytes():
    with pytest.raises(ValueError):
        strategy("bytes33")


def test_min_max_fixed():
    with pytest.raises(TypeError):
        strategy("bytes16", min_size=16)
    with pytest.raises(TypeError):
        strategy("bytes16", max_size=16)


@given(value=strategy("bytes4"))
def test_given_fixed(value):
    assert type(value) is bytes
    assert len(value) == 4


@given(value=strategy("bytes"))
def test_given_dynamic(value):
    assert type(value) is bytes
    assert 1 <= len(value) <= 64


@given(value=strategy("bytes", min_size=32))
def test_min(value):
    assert 32 <= len(value) <= 64


@given(value=strategy("bytes", max_size=6))
def test_max(value):
    assert 1 <= len(value) <= 6


@given(value=strategy("bytes", min_size=31, max_size=35))
def test_min_max(value):
    assert 31 <= len(value) <= 35


@given(value=strategy("bytes2", exclude=[b"00", b"42", b"69"]))
def test_exclude(value):
    assert value not in [b"00", b"42", b"69"]
