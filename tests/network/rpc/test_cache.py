from brownie import compile_source
from brownie.network.middlewares.caching import is_cacheable_bytecode

good_code = """
# @version ^0.2.11
@external
def foo() -> Bytes[2]:
    # caching should still be possible because the return value is stripped
    return 0xFFF4
"""

selfdestruct_code = """
pragma solidity ^0.4.22;
contract Boom{
    function innocence() {
        selfdestruct(msg.sender);
    }
}
"""

delegatecall_code = """
pragma solidity ^0.4.22;
contract BadDecision {
    function call(address a) {
        a.delegatecall(bytes4(sha3("innocence()")));
    }
}"""

factory_code = """
# @version ^0.2.11
@external
def make_forwarder(target: address) -> address:
    return create_forwarder_to(target)
"""


def test_good_code(accounts, web3):
    bytecode = compile_source(good_code).Vyper.deploy({"from": accounts[0]}).bytecode
    assert is_cacheable_bytecode(web3, bytecode)


def test_selfdestruct(accounts, web3):
    bytecode = compile_source(selfdestruct_code).Boom.deploy({"from": accounts[0]}).bytecode
    assert not is_cacheable_bytecode(web3, bytecode)


def test_dynamic_delecatecall(accounts, web3):
    bytecode = compile_source(delegatecall_code).BadDecision.deploy({"from": accounts[0]}).bytecode
    assert not is_cacheable_bytecode(web3, bytecode)


def test_factory(accounts, web3):
    factory = compile_source(factory_code).Vyper.deploy({"from": accounts[0]})
    assert is_cacheable_bytecode(web3, factory.bytecode)


def test_forwarder_to_good_code(accounts, web3):
    factory = compile_source(factory_code).Vyper.deploy({"from": accounts[0]})
    target = compile_source(good_code).Vyper.deploy({"from": accounts[0]})
    tx = factory.make_forwarder(target, {"from": accounts[0]})

    bytecode = web3.eth.get_code(tx.return_value)
    assert is_cacheable_bytecode(web3, bytecode)


def test_forwarder_to_bad_code(accounts, web3):
    factory = compile_source(factory_code).Vyper.deploy({"from": accounts[0]})
    target = compile_source(selfdestruct_code).Boom.deploy({"from": accounts[0]})
    tx = factory.make_forwarder(target, {"from": accounts[0]})

    bytecode = web3.eth.get_code(tx.return_value)
    assert not is_cacheable_bytecode(web3, bytecode)
