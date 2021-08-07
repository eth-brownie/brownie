import threading
import time

import pytest

import brownie


def send_and_wait_for_tx():
    tx = brownie.accounts[0].transfer(
        brownie.accounts[1], "0.1 ether", required_confs=0, silent=True
    )
    tx.wait(2)
    assert tx.confirmations >= 2
    assert tx.status == 1


@pytest.fixture
def block_time_network(devnetwork, config, network_name):
    """Provide a network with fixed block mining time of 1 second."""
    config.networks[network_name]["cmd_settings"]["block_time"] = 1
    devnetwork.disconnect()
    devnetwork.connect(network_name)
    yield devnetwork
    devnetwork.disconnect()


def test_required_confirmations_deploy(accounts, BrownieTester, block_time_network, web3):
    block = web3.eth.block_number
    accounts[0].deploy(BrownieTester, True, required_confs=3)
    assert web3.eth.block_number - block >= 3


def test_required_confirmations_transfer(accounts, block_time_network, web3):
    block = web3.eth.block_number
    tx = accounts[0].transfer(accounts[1], "1 ether", required_confs=3)
    assert tx.confirmations >= 3
    assert web3.eth.block_number - block >= 3


def test_required_confirmations_transact(accounts, BrownieTester, block_time_network, web3):
    block = web3.eth.block_number
    brownieTester = BrownieTester.deploy(True, {"from": accounts[0], "required_confs": 2})
    assert web3.eth.block_number - block >= 2

    block = web3.eth.block_number
    tx = brownieTester.doNothing({"from": accounts[0], "required_confs": 4})
    assert tx.confirmations >= 4
    assert web3.eth.block_number - block >= 4


def test_required_confirmations_zero(accounts, block_time_network, web3):
    block = web3.eth.block_number
    tx = accounts[0].transfer(accounts[1], "1 ether", required_confs=0)
    assert tx.status == -1
    assert web3.eth.block_number - block == 0
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


def test_pending_nonce(accounts, block_time_network):
    for _ in range(3):
        accounts[0].transfer(accounts[1], "0.1 ether", required_confs=0, silent=True)
    assert accounts[0]._pending_nonce() == 3
    assert accounts[0].nonce < 3
    time.sleep(3.5)
    assert accounts[0].nonce == 3


def test_multithreading(accounts, history, block_time_network):
    threads = []
    for _ in range(3):
        thread = threading.Thread(target=send_and_wait_for_tx, daemon=True)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    for tx in history:
        assert tx.status == 1
        assert tx.confirmations >= 2
