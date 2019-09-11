#!/usr/bin/python3


def test_adds_tx(accounts, state):
    assert len(state) == 0
    tx = accounts[0].transfer(accounts[1], "1 ether")
    assert tx in state
    assert len(state) == 1
    tx = accounts[2].transfer(accounts[1], "1 ether")
    assert state[-1] == tx
    assert len(state) == 2


def test_resets(accounts, state, rpc):
    for i in range(3):
        accounts[0].transfer(accounts[1], "1 ether")
    assert len(state) == 3
    rpc.reset()
    assert len(state) == 0
    assert not state


def test_reverts(accounts, state, rpc):
    for i in range(3):
        accounts[0].transfer(accounts[1], "1 ether")
    rpc.snapshot()
    assert len(state) == 3
    for i in range(3):
        accounts[0].transfer(accounts[1], "1 ether")
    assert len(state) == 6
    tx = state[-1]
    rpc.revert()
    assert len(state) == 3
    assert tx not in state


def test_from(accounts, state):
    for i in range(1, 4):
        accounts[0].transfer(accounts[i], "1 ether")
    assert len(state.from_sender(accounts[0])) == 3
    assert len(state.from_sender(accounts[1])) == 0


def test_to(accounts, state):
    for i in range(1, 4):
        accounts[0].transfer(accounts[i], "1 ether")
    assert len(state.to_receiver(accounts[0])) == 0
    assert len(state.to_receiver(accounts[1])) == 1
    assert len(state.to_receiver(accounts[2])) == 1
    assert len(state.to_receiver(accounts[3])) == 1


def test_of(accounts, state):
    for i in range(4):
        accounts[0].transfer(accounts[i], "1 ether")
    assert len(state.of_address(accounts[0])) == 4
    assert len(state.of_address(accounts[1])) == 1
    assert len(state.of_address(accounts[2])) == 1
    assert len(state.of_address(accounts[3])) == 1


def test_copy(accounts, state, rpc):
    accounts[0].transfer(accounts[1], "1 ether")
    h = state.copy()
    assert type(h) is list
    assert len(h) == 1
    assert h[0] == state[0]
    rpc.reset()
    assert len(h) == 1
