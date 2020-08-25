#!/usr/bin/python3

from brownie import Wei, compile_source
from brownie.convert import EthAddress


def test_to_eoa(accounts):
    container = compile_source(
        """
# @version 0.2.4

@external
@payable
def send_ether(receivers: address[3]) -> bool:
    value: uint256 =100
    for i in range(3):
        send(receivers[i], value)
        value += 100
    return True"""
    ).Vyper
    contract = container.deploy({"from": accounts[0]})
    tx = contract.send_ether(accounts[:3], {"value": 800})
    assert tx.internal_transfers == [
        {"from": contract, "to": accounts[0], "value": 100},
        {"from": contract, "to": accounts[1], "value": 200},
        {"from": contract, "to": accounts[2], "value": 300},
    ]


def test_to_contract(accounts):
    container = compile_source(
        """
# @version 0.2.4

@external
@payable
def send_ether(receiver: address) -> bool:
    send(receiver, msg.value)
    return True

@external
@payable
def __default__():
    return
    """
    ).Vyper
    contract = container.deploy({"from": accounts[0]})
    contract2 = container.deploy({"from": accounts[0]})
    tx = contract.send_ether(contract2, {"value": 31337})

    assert tx.internal_transfers == [{"from": contract, "to": contract2, "value": 31337}]


def test_types(accounts):
    container = compile_source(
        """
# @version 0.2.4

@external
@payable
def send_ether(receiver: address) -> bool:
    send(receiver, msg.value)
    return True"""
    ).Vyper
    contract = container.deploy({"from": accounts[0]})
    tx = contract.send_ether(accounts[1], {"value": 800})
    xfer = tx.internal_transfers[0]
    assert type(xfer["from"]) is EthAddress
    assert type(xfer["to"]) is EthAddress
    assert type(xfer["value"]) is Wei


def test_via_create_vyper(accounts):
    container = compile_source(
        """
# @version 0.2.4

@external
@payable
def send_ether() -> bool:
    x: address = create_forwarder_to(self, value=msg.value)
    return True"""
    ).Vyper
    contract = container.deploy({"from": accounts[0]})
    tx = contract.send_ether({"value": 42})
    assert tx.internal_transfers == [{"from": contract, "to": tx.new_contracts[0], "value": 42}]


def test_via_create_solidity(accounts):
    project = compile_source(
        """pragma solidity 0.6.2;

contract Foo { constructor () public payable {} }

contract Deployer {
    function create () public payable returns (Foo) { return new Foo{value: msg.value}(); }
}"""
    )
    contract = project.Deployer.deploy({"from": accounts[0]})
    tx = contract.create({"value": 69})
    assert tx.internal_transfers == [{"from": contract, "to": tx.new_contracts[0], "value": 69}]
