#!/usr/bin/python3

import pytest

from brownie import accounts, compile_source
from brownie.exceptions import UndeployedLibrary

source = """pragma solidity ^0.5.0;

library TestLib {

    function linkMethod(
        uint _value,
        uint _multiplier
    )
        public
        pure
        returns (uint)
    {
        return _value * _multiplier;
    }
}

contract Unlinked {

    function callLibrary(uint amount, uint multiple) external view returns (uint) {
        return TestLib.linkMethod(amount, multiple);
    }
}
"""


def test_unlinked_library(devnetwork):
    project = compile_source(source)
    with pytest.raises(UndeployedLibrary):
        accounts[0].deploy(project['Unlinked'])
    lib = accounts[0].deploy(project['TestLib'])
    meta = accounts[0].deploy(project['Unlinked'])
    assert lib.address[2:].lower() in meta.bytecode
