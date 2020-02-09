#!/usr/bin/python3

test_source = """
def test_rpc(state_machine):
    assert True

def test_web3():
    assert False
    """


def test_stateful_flag(plugintester):
    result = plugintester.runpytest()
    result.assert_outcomes(passed=1, failed=1)
    result = plugintester.runpytest("--stateful=false")
    result.assert_outcomes(skipped=1, failed=1)
    result = plugintester.runpytest("--stateful=true")
    result.assert_outcomes(skipped=1, passed=1)


def test_stateful_flag_xdist(isolatedtester):
    result = isolatedtester.runpytest("-n 2")
    result.assert_outcomes(passed=1, failed=1)
    result = isolatedtester.runpytest("-n 2", "--stateful=false")
    result.assert_outcomes(skipped=1, failed=1)
    result = isolatedtester.runpytest("-n 2", "--stateful=true")
    result.assert_outcomes(skipped=1, passed=1)
