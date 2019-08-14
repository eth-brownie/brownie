#!/usr/bin/python3

import pytest

from brownie import compile_source

source = """pragma solidity ^0.5.0;

library TestLib {

    function linkMethod(uint a, uint b) public pure returns (uint) {
        return a * b;
    }

}

contract Unlinked {

    function callLibrary(uint amount, uint multiple) external returns (uint) {
        return TestLib.linkMethod(amount, multiple);
    }

}
"""


@pytest.fixture
def librarytester(devnetwork):
    compiled = compile_source(source)
    return compiled


@pytest.fixture
def librarytester2(devnetwork):
    compiled = compile_source(source)
    return compiled
