import pytest

from brownie import compile_source

solidity_source = """
pragma solidity >=0.6.0;

contract Foo {
    address constant TARGET = 0xD0660cD418a64a1d44E9214ad8e459324D8157f1;

    function foo_call() external {
        TARGET.call(abi.encodeWithSignature("bar()"));
    }

    function foo_staticcall() external {
        TARGET.staticcall(abi.encodeWithSignature("bar()"));
    }

    function foo_delegatecall() external {
        TARGET.delegatecall(abi.encodeWithSignature("bar()"));
    }
}
"""


vyper_source = """
# @version 0.2.15


TARGET: constant(address) = 0xD0660cD418a64a1d44E9214ad8e459324D8157f1


@external
def foo_call():
    raw_call(TARGET, method_id("bar()"))


@external
def foo_staticcall():
    raw_call(TARGET, method_id("bar()"), is_static_call=True)


@external
def foo_delegatecall():
    raw_call(TARGET, method_id("bar()"), is_delegate_call=True)
"""


@pytest.fixture()
def solidity_contract(accounts):
    container = compile_source(solidity_source)
    return container.Foo.deploy({"from": accounts[0]})


@pytest.fixture()
def vyper_contract(accounts):
    container = compile_source(vyper_source, vyper_version="0.2.15").Vyper
    return container.deploy({"from": accounts[0]})


@pytest.fixture(params=[True, False], ids=["SolFoo", "VyFoo"])
def foo_contract(request, solidity_contract, vyper_contract):
    return solidity_contract if request.param else vyper_contract


@pytest.mark.parametrize("low_level_method", ["call", "staticcall", "delegatecall"])
def test_calls_to_empty_accounts(foo_contract, low_level_method):
    method = f"foo_{low_level_method}"
    tx = getattr(foo_contract, method).transact()

    expected_dict = {
        "from": foo_contract.address,
        "to": "0xD0660cD418a64a1d44E9214ad8e459324D8157f1",
        "op": low_level_method.upper(),
        "calldata": "0xfebb0f7e",  # keccak256("bar()")[:4]
    }

    # call opcode transmits value as well
    if low_level_method == "call":
        expected_dict["value"] = 0

    assert len(tx.subcalls) == 1
    assert tx.subcalls[-1] == expected_dict
