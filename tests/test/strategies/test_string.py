#!/usr/bin/python3

from hypothesis import given
from hypothesis.strategies import SearchStrategy

from brownie.test import strategy


def test_strategy():
    assert isinstance(strategy("string"), SearchStrategy)


@given(value=strategy("string"))
def test_given(value):
    assert type(value) is str
    assert 0 <= len(value) <= 64


@given(value=strategy("string", min_size=32))
def test_min(value):
    assert 32 <= len(value) <= 64


@given(value=strategy("string", max_size=16))
def test_max(value):
    assert 0 <= len(value) <= 16


@given(value=strategy("string", min_size=4, max_size=8))
def test_min_max(value):
    assert 4 <= len(value) <= 8
