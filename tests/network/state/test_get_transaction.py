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
