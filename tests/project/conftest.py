#!/usr/bin/python3

from pathlib import Path

import pytest

test_source = """
pragma solidity [VERSION];

library Bar {
    function baz(uint a, uint b) external pure returns (uint) {
        return a + b;
    }
}

contract Foo {

    address payable owner;

    function baz(uint a, uint b) external view returns (uint) {
        return Bar.baz(a, b);
    }
}
"""


@pytest.fixture(scope="session")
def btsource():
    path = Path(__file__).parent.joinpath(
        "../data/brownie-test-project/contracts/BrownieTester.sol"
    )
    with path.open() as fs:
        return fs.read()


@pytest.fixture(scope="session")
def solc6source():
    return test_source.replace("[VERSION]", "^0.6.0")


@pytest.fixture(scope="session")
def solc5source():
    return test_source.replace("[VERSION]", "^0.5.0")


@pytest.fixture(scope="session")
def solc4source():
    source = test_source.replace("payable ", "")
    source = source.replace("[VERSION]", "^0.4.25")
    return source


@pytest.fixture(scope="session")
def vysource():
    return """
# comments are totally kickass
# @version 0.2.4
@external
def test() -> bool:
    return True
"""
