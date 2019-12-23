#!/usr/bin/python3

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


@pytest.fixture()
def btsource(testproject):
    path = testproject._path.joinpath("contracts/BrownieTester.sol")
    with path.open() as fs:
        return fs.read()


@pytest.fixture
def solc6source():
    return test_source.replace("[VERSION]", "^0.6.0")


@pytest.fixture
def solc5source():
    return test_source.replace("[VERSION]", "^0.5.0")


@pytest.fixture
def solc4source():
    source = test_source.replace("payable ", "")
    source = source.replace("[VERSION]", "^0.4.25")
    return source
