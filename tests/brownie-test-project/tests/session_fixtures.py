#!/usr/bin/python3

import brownie
from brownie import project


def test_accounts(accounts, a):
    assert a == accounts
    assert accounts == brownie.accounts


def test_history(history):
    assert history == brownie.history


def test_rpc(rpc):
    assert rpc == brownie.rpc


def test_web3(web3):
    assert web3 == brownie.web3


def test_contract_container(Token, CoverageTester):
    assert Token == project.Token
    assert CoverageTester == project.CoverageTester
