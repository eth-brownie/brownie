#!/usr/bin/python3

import pytest

isolation_source = '''import pytest

@pytest.fixture(autouse=True)
def isolation({0}_isolation):
    pass

@pytest.fixture(scope="module", autouse=True)
def setup(accounts):
    accounts[0].transfer(accounts[1], "1 ether")

def test_isolation_first(accounts, web3):
    assert web3.eth.block_number == 1
    assert accounts[1].balance() == "101 ether"
    accounts[0].transfer(accounts[1], "1 ether")

def test_isolation_second(accounts, web3):
    assert web3.eth.block_number == {1}
    assert accounts[1].balance() == "10{1} ether"'''


@pytest.mark.parametrize("arg", ["", "-n 2"])
def test_fn_isolation(plugintester, web3, arg):
    plugintester.makepyfile(isolation_source.format("fn", 1))
    result = plugintester.runpytest_inprocess(arg)
    result.assert_outcomes(passed=2)
    assert web3.eth.block_number == 0


@pytest.mark.parametrize("arg", ["", "-n 2"])
def test_module_isolation(plugintester, web3, arg):
    plugintester.makepyfile(isolation_source.format("module", 2))
    result = plugintester.runpytest_inprocess(arg)
    result.assert_outcomes(passed=2)
    assert web3.eth.block_number == 0


def test_xdist_no_isolation(plugintester):
    plugintester.makepyfile("def test_nothing(): assert True")
    result = plugintester.runpytest()
    result.assert_outcomes(passed=1)
    result = plugintester.runpytest_subprocess("-n 1")
    assert "xdist workers failed to collect tests" in result.errlines[0]
