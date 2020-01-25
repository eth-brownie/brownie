#!/usr/bin/python3

import warnings

from hypothesis.strategies import SearchStrategy

from brownie.network.account import Account
from brownie.test import strategy


def test_strategy():
    assert isinstance(strategy("address"), SearchStrategy)


def test_given(accounts):
    # cannot test against @given because when accounts is empty during test generation
    st = strategy("address")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        assert st.example() in accounts
        assert isinstance(st.example(), Account)
