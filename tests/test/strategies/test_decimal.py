#!/usr/bin/python3

from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis.strategies import SearchStrategy

from brownie.test import strategy


def test_strategy():
    assert isinstance(strategy("decimal"), SearchStrategy)
    assert isinstance(strategy("fixed168x10"), SearchStrategy)


def test_invalid_min_max():
    # min too low
    with pytest.raises(ValueError):
        strategy("decimal", min_value=-(2**128))
    # max too high
    with pytest.raises(ValueError):
        strategy("decimal", max_value=2**128)
    # min > max
    with pytest.raises(ValueError):
        strategy("decimal", min_value=42, max_value=12)


@given(value=strategy("decimal"))
def test_given(value):
    assert type(value) is Decimal
    assert value.as_tuple().exponent >= -10
    assert -(2**127) <= value <= 2**127 - 1


@given(value=strategy("decimal", min_value=1, max_value="1.5"))
def test_min_max(value):
    assert 1 <= value <= 1.5


@given(value=strategy("decimal", min_value="1.23", max_value="1.35", exclude=[1.337, 1.2345]))
def test_exclude(value):
    assert value not in [1.337, 1.2345]
