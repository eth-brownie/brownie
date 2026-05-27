#!/usr/bin/python3

import pytest

from brownie import compile_source
from brownie.network.web3 import ENS, _ens_cache, web3

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


class _FakeENS:
    def __init__(self, records):
        self.records = records

    def address(self, domain):
        result = self.records[domain]
        if isinstance(result, Exception):
            raise result
        return result


@pytest.fixture
def fake_ens(monkeypatch, tmp_path):
    original_cache = dict(_ens_cache)
    _ens_cache.clear()
    monkeypatch.setattr(web3, "_mainnet_w3", object())

    def apply(records):
        monkeypatch.setattr(ENS, "from_web3", lambda _: _FakeENS(records))

    yield apply

    _ens_cache.clear()
    _ens_cache.update(original_cache)


@pytest.fixture
def librarytester(devnetwork):
    compiled = compile_source(source)
    return compiled


@pytest.fixture
def librarytester2(devnetwork):
    compiled = compile_source(source)
    return compiled
