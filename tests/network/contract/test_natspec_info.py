import pytest

from brownie.project import compile_source

solc_natspec = """
pragma solidity >=0.5.0;

/**
    @title A simulator for Bug Bunny, the most famous Rabbit
    @author Warned Bros
    @notice You can use this contract for only the most basic simulation
    @dev
        Simply chewing a carrot does not count, carrots must pass
        the throat to be considered eaten
 */
contract Bugs {
    /**
        @notice Determine if Bugs will accept `qty` of `food` to eat
        @dev Compares the entire string and does not rely on a hash
        @param food The name of a food to evaluate (in English)
        @param qty The number of food items to evaluate
        @return True if Bugs will eat it, False otherwise
        @return A second value for testing purposes
     */
    function doesEat(uint256 food, uint256 qty) external returns (bool, bool) {
        return (true, false);
    }
}
"""

vyper_natspec = '''
"""
@title A simulator for Bug Bunny, the most famous Rabbit
@author Warned Bros
@notice You can use this contract for only the most basic simulation
@dev
    Simply chewing a carrot does not count, carrots must pass
    the throat to be considered eaten
"""

@external
@payable
def doesEat(food: String[30], qty: uint256) -> (bool, bool):
    """
    @notice Determine if Bugs will accept `qty` of `food` to eat
    @dev Compares the entire string and does not rely on a hash
    @param food The name of a food to evaluate (in English)
    @param qty The number of food items to evaluate
    @return True if Bugs will eat it, False otherwise
    @return A second value for testing purposes
    """
    return True, False
'''


@pytest.mark.parametrize("version", [5, 6])
def test_solc_contract(version, capfd):
    code = solc_natspec
    contract = compile_source(code, solc_version=f"0.{version}.0").Bugs

    contract.info()

    out = capfd.readouterr()[0]
    for field in ("title", "author", "notice", "details"):
        assert f"@{field}" in out


@pytest.mark.parametrize("version", [5, 6])
def test_solc_function(version, capfd, accounts):
    code = solc_natspec
    contract = compile_source(code, solc_version=f"0.{version}.0").Bugs
    contract.deploy({"from": accounts[0]})

    contract[0].doesEat.info()

    out = capfd.readouterr()[0]
    for field in ("notice", "details"):
        assert f"@{field}" in out

    assert out.count("@param") == 2
    assert out.count("@return") == 2 if version == 6 else 1


def test_vyper_contract(capfd):
    code = vyper_natspec
    contract = compile_source(code).Vyper

    contract.info()

    out = capfd.readouterr()[0]
    for field in ("title", "author", "notice", "details"):
        assert f"@{field}" in out


def test_vyper_function(capfd, accounts):
    code = vyper_natspec
    contract = compile_source(code).Vyper
    contract.deploy({"from": accounts[0]})

    contract[0].doesEat.info()

    out = capfd.readouterr()[0]
    for field in ("notice", "details"):
        assert f"@{field}" in out

    assert out.count("@param") == 2
    assert out.count("@return") == 2
