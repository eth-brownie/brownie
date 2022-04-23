#!/usr/bin/python3

from brownie import compile_source


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


def test_block_identifier(accounts, history):
    contract = compile_source(
        """
# @version 0.2.4
foo: public(int128)

@external
def set_foo(_foo: int128):
    self.foo = _foo
    """
    ).Vyper.deploy({"from": accounts[0]})

    contract.set_foo(13)
    contract.set_foo(42)

    assert contract.foo() == 42
    assert contract.foo(block_identifier=history[-2].block_number) == 13
    assert contract.foo.call(block_identifier=history[-2].block_number) == 13


def test_always_transact(accounts, tester, argv, web3, monkeypatch, history):
    owner = tester.owner()
    argv["always_transact"] = True
    height = web3.eth.block_number
    result = tester.owner()

    assert owner == result
    assert web3.eth.block_number == height == len(history)

    monkeypatch.setattr("brownie.network.chain.undo", lambda: None)
    result = tester.owner()
    tx = history[-1]

    assert owner == result
    assert web3.eth.block_number == height + 1 == len(history)
    assert tx.fn_name == "owner"


def test_always_transact_block_identifier(accounts, tester, argv, web3, monkeypatch, history):
    argv["always_transact"] = True
    height = web3.eth.block_number
    last_tx = history[-1]

    monkeypatch.setattr("brownie.network.chain.undo", lambda: None)
    tester.owner(block_identifier="latest")

    # using `block_identifier` should take priority over `always_transact`
    assert web3.eth.block_number == height
    assert last_tx == history[-1]


def test_nonce_manual_call(tester, accounts):
    """manual nonce is ignored when calling without transact"""
    nonce = accounts[0].nonce
    tx = tester.getTuple(accounts[0], {"from": accounts[0], "nonce": 5})
    assert not hasattr(tx, "nonce")
    assert accounts[0].nonce == nonce


def test_nonce_manual_transact(tester, accounts):
    """correct manual nonce with transact"""
    nonce = accounts[0].nonce
    tx = tester.getTuple.transact(accounts[0], {"from": accounts[0], "nonce": nonce})
    assert tx.nonce == nonce
    assert accounts[0].nonce == nonce + 1


# this behaviour changed in ganache7, if the test suite is updated to work
# in hardhat we should still include it

# @pytest.mark.parametrize("nonce", (-1, 1, 15))
# def test_rasises_on_incorrect_nonce_manual_transact(tester, accounts, nonce):
#     """raises on incorrect manual nonce with transact"""
#     nonce += accounts[0].nonce
#     with pytest.raises(ValueError):
#         tester.getTuple.transact(accounts[0], {"from": accounts[0], "nonce": nonce})


def test_tuples(tester, accounts):
    value = ["blahblah", accounts[1], ["yesyesyes", "0x1234"]]
    tester.setTuple(value)
    assert tester.getTuple(accounts[1], {"from": accounts[0]}) == value


def test_default_owner_with_coverage(tester, coverage_mode, accounts, config):
    config.active_network["settings"]["default_contract_owner"] = False
    tester.getTuple(accounts[0])
