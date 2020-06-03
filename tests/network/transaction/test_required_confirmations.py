import time

import pytest


@pytest.fixture
def block_time_network(devnetwork, config):
    """Provide a network with fixed block mining time of 1 second."""
    config.networks["development"]["cmd_settings"]["block_time"] = 1
    devnetwork.disconnect()
    devnetwork.connect("development")
    yield devnetwork
    devnetwork.disconnect()


def test_required_confirmations_deploy(accounts, BrownieTester, block_time_network, web3):
    block = web3.eth.blockNumber
    accounts[0].deploy(BrownieTester, True, required_confs=3)
    assert web3.eth.blockNumber - block >= 3


def test_required_confirmations_transfer(accounts, block_time_network, web3):
    block = web3.eth.blockNumber
    tx = accounts[0].transfer(accounts[1], "1 ether", required_confs=3)
    assert tx.confirmations >= 3
    assert web3.eth.blockNumber - block >= 3


def test_required_confirmations_transact(accounts, BrownieTester, block_time_network, web3):
    block = web3.eth.blockNumber
    brownieTester = BrownieTester.deploy(True, {"from": accounts[0], "required_confs": 2})
    assert web3.eth.blockNumber - block >= 2

    block = web3.eth.blockNumber
    tx = brownieTester.doNothing({"from": accounts[0], "required_confs": 4})
    assert tx.confirmations >= 4
    assert web3.eth.blockNumber - block >= 4


def test_required_confirmations_zero(accounts, block_time_network, web3):
    block = web3.eth.blockNumber
    tx = accounts[0].transfer(accounts[1], "1 ether", required_confs=0)
    assert tx.status == -1
    assert web3.eth.blockNumber - block == 0
    time.sleep(1.5)
    assert tx.status == 1
    assert tx.confirmations >= 1


def test_wait_for_confirmations(accounts, block_time_network):
    tx = accounts[0].transfer(accounts[1], "1 ether", required_confs=1)
    tx.wait(3)
    assert tx.confirmations in [3, 4]
    tx.wait(2)
    tx.wait(5)
    assert tx.confirmations >= 5
