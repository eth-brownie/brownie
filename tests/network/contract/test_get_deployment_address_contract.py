from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from brownie import compile_source

source = """
pragma solidity ^0.7.0;

contract Bar {
    function add(uint256 a, uint256 b) external pure returns (uint256) {
        return a + b;
    }
}

contract Foo {
    function deployBar() external returns (Bar) {
        return new Bar();
    }
}
"""


@given(st_privkey=st.binary(min_size=32, max_size=32))
@settings(max_examples=25, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_contract_get_deployment_address(accounts, st_privkey):
    assume(int(st_privkey.hex(), 16))

    # we use a different acct to deploy Foo each time
    Foo = compile_source(source).Foo
    acct = accounts.add(st_privkey)
    contract = Foo.deploy({"from": acct})

    # contract nonce starts at 1
    for i in range(1, 6):
        assert contract.deployBar({"from": acct}).return_value == contract.get_deployment_address(i)
