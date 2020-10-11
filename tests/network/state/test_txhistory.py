#!/usr/bin/python3


def test_adds_tx(accounts, history):
    assert len(history) == 0
    tx = accounts[0].transfer(accounts[1], "1 ether")
    assert tx in history
    assert len(history) == 1
    tx = accounts[2].transfer(accounts[1], "1 ether")
    assert history[-1] == tx
    assert len(history) == 2


def test_resets(accounts, history, chain):
    for i in range(3):
        accounts[0].transfer(accounts[1], "1 ether")
    assert len(history) == 3
    chain.reset()
    assert len(history) == 0
    assert not history


def test_reverts(accounts, history, chain):
    for i in range(3):
        accounts[0].transfer(accounts[1], "1 ether")
    chain.snapshot()
    assert len(history) == 3
    for i in range(3):
        accounts[0].transfer(accounts[1], "1 ether")
    assert len(history) == 6
    tx = history[-1]
    chain.revert()
    assert len(history) == 3
    assert tx not in history


def test_from(accounts, history):
    for i in range(1, 4):
        accounts[0].transfer(accounts[i], "1 ether")
    assert len(history.from_sender(accounts[0])) == 3
    assert len(history.from_sender(accounts[1])) == 0


def test_to(accounts, history):
    for i in range(1, 4):
        accounts[0].transfer(accounts[i], "1 ether")
    assert len(history.to_receiver(accounts[0])) == 0
    assert len(history.to_receiver(accounts[1])) == 1
    assert len(history.to_receiver(accounts[2])) == 1
    assert len(history.to_receiver(accounts[3])) == 1


def test_of(accounts, history):
    for i in range(4):
        accounts[0].transfer(accounts[i], "1 ether")
    assert len(history.of_address(accounts[0])) == 4
    assert len(history.of_address(accounts[1])) == 1
    assert len(history.of_address(accounts[2])) == 1
    assert len(history.of_address(accounts[3])) == 1


def test_copy(accounts, history, chain):
    accounts[0].transfer(accounts[1], "1 ether")
    h = history.copy()
    assert type(h) is list
    assert len(h) == 1
    assert h[0] == history[0]
    chain.reset()
    assert len(h) == 1


def test_filter(accounts, history):
    tx1 = accounts[0].transfer(accounts[1], "1 ether")
    tx2 = accounts[1].transfer(accounts[2], "2 ether")
    tx3 = accounts[0].transfer(accounts[2], "3 ether")

    assert history.filter(sender=accounts[0]) == [tx1, tx3]
    assert history.filter(sender=accounts[1], receiver=accounts[2]) == [tx2]
    assert history.filter(sender=accounts[0], key=lambda k: k.value > "1 ether") == [tx3]
