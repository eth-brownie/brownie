from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from brownie import compile_source


@given(st_privkey=st.binary(min_size=32, max_size=32))
@settings(max_examples=25, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_get_deployment_address(accounts, st_privkey):
    assume(int(st_privkey.hex(), 16))

    Foo = compile_source("""pragma solidity ^0.6.0; contract Foo {}""").Foo
    acct = accounts.add(st_privkey)

    for i in range(5):
        expected = acct.get_deployment_address(i)
        contract = Foo.deploy({"from": acct})
        assert contract.address == expected


def test_default_nonce(accounts):
    for i in range(5):
        assert accounts[0].get_deployment_address() == accounts[0].get_deployment_address(i)
        accounts[0].transfer(accounts[0], 0)
