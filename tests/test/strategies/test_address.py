#!/usr/bin/python3

from hypothesis import HealthCheck, given, settings
from hypothesis.strategies._internal.deferred import DeferredStrategy

from brownie.network.account import Account
from brownie.test import strategy


def test_strategy():
    assert isinstance(strategy("address"), DeferredStrategy)


@given(value=strategy("address"))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_given(accounts, value):
    assert value in accounts
    assert isinstance(value, Account)


@given(value=strategy("address", length=3))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_length(accounts, value):
    assert list(accounts).index(value) < 3


def test_repr():
    assert repr(strategy("address")) == "sampled_from(accounts)"
