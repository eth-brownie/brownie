#!/usr/bin/python3


def test_attributes(accounts, tester):
    assert tester.getTuple._address == tester.address
    assert tester.getTuple._name == "BrownieTester.getTuple"
    assert tester.getTuple._owner == accounts[0]
    assert type(tester.getTuple.abi) is dict
    assert tester.getTuple.signature == "0x2e271496"


def test_encode_input(tester):
    data = tester.getTuple.encode_input("0x2f084926Fd8A120089cA5F622975Fe7F1306AFF9")
    assert data == "0x2e2714960000000000000000000000002f084926fd8a120089ca5f622975fe7f1306aff9"


def test_transact(accounts, tester):
    nonce = accounts[0].nonce
    tx = tester.getTuple.transact(accounts[0], {"from": accounts[0]})
    assert tx.return_value == tester.getTuple(accounts[0])
    assert accounts[0].nonce == nonce + 1


def test_always_transact(accounts, tester, argv, web3, monkeypatch, history):
    owner = tester.owner()
    argv["always_transact"] = True
    height = web3.eth.blockNumber
    result = tester.owner()
    assert owner == result
    assert web3.eth.blockNumber == height == len(history)
    monkeypatch.setattr("brownie.network.rpc.undo", lambda: None)
    result = tester.owner()
    tx = history[-1]
    assert owner == result
    assert web3.eth.blockNumber == height + 1 == len(history)
    assert tx.fn_name == "owner"


def test_tuples(tester, accounts):
    value = ["blahblah", accounts[1], ["yesyesyes", "0x1234"]]
    tester.setTuple(value)
    assert tester.getTuple(accounts[1], {"from": accounts[0]}) == value


def test_default_owner_with_coverage(tester, coverage_mode, accounts, config):
    config.active_network["settings"]["default_contract_owner"] = False
    tester.getTuple(accounts[0])
