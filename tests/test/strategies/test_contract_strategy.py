#!/usr/bin/python3

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis.strategies._internal.deferred import DeferredStrategy

from brownie.network.contract import ProjectContract
from brownie.test import contract_strategy


def test_strategy():
    assert isinstance(contract_strategy("ERC20"), DeferredStrategy)


def test_repr():
    assert repr(contract_strategy("Token")) == "sampled_from(Token)"


def test_does_not_exist():
    with pytest.raises(NameError):
        contract_strategy("Foo").validate()


@given(contract=contract_strategy("BrownieTester"))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_given(tester, contract):
    assert isinstance(contract, ProjectContract)
