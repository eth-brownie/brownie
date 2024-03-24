test_source = """
import pytest

@pytest.mark.require_network("development")
def test_require_network_pass():
    # should run because we are connected to development
    pass

@pytest.mark.require_network("goerli")
def test_require_network_skip():
    # should skip because we are not connected to goerli
    pass

@pytest.mark.require_network
def test_require_network_error():
    # should error because no network was given
    pass
    """


def test_require_network(plugintester):
    result = plugintester.runpytest()
    result.assert_outcomes(skipped=1, passed=1, errors=1)


def test_require_network_xdist(isolatedtester):
    result = isolatedtester.runpytest("-n 2")
    result.assert_outcomes(skipped=1, passed=1, errors=1)
