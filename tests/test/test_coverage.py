#!/usr/bin/python3

from brownie.test import coverage
from brownie.network import accounts, history


def test_analyze(token):
    token.transfer(accounts[1], 1000, {'from': accounts[0]})
    cov = coverage.analyze(history[-1:])
    assert cov['Token']['statements']['contracts/Token.sol'] == {10, 11, 12, 13}
    assert cov['Token']['statements']['contracts/SafeMath.sol'] == {15, 16, 17, 18}


def test_merge(token):
    token.transfer(accounts[1], 1000, {'from': accounts[0]})
    cov = coverage.analyze(history[-1:])
    token.approve(accounts[1], 1000, {'from': accounts[0]})
    cov2 = coverage.analyze(history[-1:])
    merged = coverage.merge([cov, cov2])
    assert cov['Token']['statements']['contracts/Token.sol'] == {10, 11, 12, 13}
    assert cov2['Token']['statements']['contracts/Token.sol'] == {1, 2, 3}
    assert merged['Token']['statements']['contracts/Token.sol'] == {1, 2, 3, 10, 11, 12, 13}


# split_by_fn

# get_totals

# get_highlights
