import pytest
from web3.exceptions import TransactionNotFound


def test_exists_in_history(accounts, chain, history):
    tx = accounts[0].transfer(accounts[1], 1000)
    assert chain.get_transaction(tx.txid) == tx


def test_not_in_history(accounts, chain, history):
    tx = accounts[0].transfer(accounts[1], 1000)
    history._list.clear()
    othertx = chain.get_transaction(tx.txid)

    assert tx != othertx
    assert tx.txid == othertx.txid


def test_unknown_tx(accounts, chain, history):
    with pytest.raises(TransactionNotFound):
        chain.get_transaction("0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421")


def test_external_tx(network, chain):
    network.connect("mainnet")

    tx = chain.get_transaction("0x1e0e3df9daa09d009185a1d009b905a9264e296f2d9c8cf6e8a2d0723df249a3")
    assert tx.status == 1


def test_external_tx_reverted(network, chain):
    network.connect("mainnet")

    tx = chain.get_transaction("0x7c913d12a7692889c364913b7909806de05692abc9312b718f16f444e4a6b94b")
    assert tx.status == 0
