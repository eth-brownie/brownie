#!/usr/bin/python3

import pytest
from hypothesis import given
from hypothesis.strategies import SearchStrategy

from brownie.test import strategy


def test_strategy():
    assert isinstance(strategy("bool"), SearchStrategy)


def test_kwargs():
    with pytest.raises(TypeError):
        strategy("bool", excludes=[True])


@given(value=strategy("bool"))
def test_given(value):
    assert type(value) is bool
