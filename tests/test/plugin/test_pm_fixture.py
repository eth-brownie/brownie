from brownie.project.main import install_package

test_source = """
import pytest

@pytest.fixture
def token(pm, accounts):
    Token = pm('brownie-mix/token-mix@1.0.0').Token
    yield Token.deploy("Test", "TST", 18, 100000, {'from': accounts[0]})

def test_token(token, accounts):
    token.transfer(accounts[1], 100, {'from': accounts[0]})
    """


def test_pm_fixture(plugintester):
    install_package("brownie-mix/token-mix@1.0.0")
    result = plugintester.runpytest()
    result.assert_outcomes(passed=1)
