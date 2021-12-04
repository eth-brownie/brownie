from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from brownie import compile_source, web3

source = """
pragma solidity ^0.7.0;

contract Bar {
    function add(uint256 a, uint256 b) external pure returns (uint256) {
        return a + b;
    }
}

contract Foo {
    function deployBar(bytes32 salt) external returns (Bar) {
        return new Bar{salt: salt}();
    }
}
"""


@given(st_privkey=st.binary(min_size=32, max_size=32))
@settings(max_examples=25, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_calculate_deterministic_address(accounts, st_privkey):
    assume(int(st_privkey.hex(), 16))

    # we use a different acct to deploy Foo each time
    Foo = compile_source(source).Foo
    Bar = compile_source(source).Bar
    acct = accounts.add(st_privkey)
    contract = Foo.deploy({"from": acct})

    for i in range(5):
        salt = web3.keccak(i)
        addr = contract.deployBar(salt, {"from": acct}).return_value
        assert addr == contract.calculate_deterministic_address(salt, Bar.deploy.encode_input())
