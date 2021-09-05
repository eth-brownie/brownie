import inspect

from lazy_object_proxy import Proxy

import brownie


def test_auto_deploy_on_testnet(config, devnetwork):
    with brownie.multicall:
        # gets deployed on init
        assert "multicall2" in config.active_network
        addr = config.active_network["multicall2"]

    with brownie.multicall:
        # uses the previously deployed instance
        assert config.active_network["multicall2"] == addr


def test_proxy_object_is_returned_from_calls(accounts, tester):
    addr = accounts[1]
    value = ["blahblah", addr, ["yesyesyes", "0x1234"]]
    tester.setTuple(value)

    with brownie.multicall:
        # the value hasn't been fetched so ret_value is just the proxy
        # but if we access ret_val again it will update
        # so use getattr_static to see it has yet to update
        ret_val = tester.getTuple(addr)
        assert inspect.getattr_static(ret_val, "__wrapped__") != value
        assert isinstance(ret_val, Proxy)
        assert ret_val.__wrapped__ == value


def test_flush_mid_execution(accounts, tester):
    addr = accounts[1]
    value = ["blahblah", addr, ["yesyesyes", "0x1234"]]
    tester.setTuple(value)

    with brownie.multicall:
        tester.getTuple(addr)
        assert len([x for v in brownie.multicall._pending_calls.values() for x in v]) == 1
        brownie.multicall.flush()
        assert len([x for v in brownie.multicall._pending_calls.values() for x in v]) == 0


def test_proxy_object_fetches_on_next_use(accounts, tester):
    addr = accounts[1]
    value = ["blahblah", addr, ["yesyesyes", "0x1234"]]
    tester.setTuple(value)

    with brownie.multicall:
        ret_val = tester.getTuple(addr)
        assert len([x for v in brownie.multicall._pending_calls.values() for x in v]) == 1
        # ret_val is now fetched
        assert ret_val == value
        assert len([x for v in brownie.multicall._pending_calls.values() for x in v]) == 0


def test_proxy_object_updates_on_exit(accounts, tester):
    addr = accounts[1]
    value = ["blahblah", addr, ["yesyesyes", "0x1234"]]
    tester.setTuple(value)

    with brownie.multicall:
        ret_val = tester.getTuple(addr)

    assert ret_val == value


def test_standard_calls_passthrough(accounts, tester):
    addr = accounts[1]
    value = ["blahblah", addr, ["yesyesyes", "0x1234"]]
    tester.setTuple(value)

    with brownie.multicall:
        assert tester.getTuple.call(addr) == value
        assert not isinstance(tester.getTuple.call(addr), Proxy)


def test_standard_calls_work_after_context(accounts, tester):
    addr = accounts[1]
    value = ["blahblah", addr, ["yesyesyes", "0x1234"]]
    tester.setTuple(value)

    with brownie.multicall:
        assert tester.getTuple(addr) == value

    assert tester.getTuple(addr) == value
    assert not isinstance(tester.getTuple(addr), Proxy)


def test_deploy_staticmethod(accounts, config):
    multicall = brownie.multicall.deploy({"from": accounts[0]})
    assert config.active_network["multicall2"] == multicall.address


def test_using_block_identifier(accounts, tester):
    # need to deploy before progressing chain
    brownie.multicall.deploy({"from": accounts[0]})

    addr = accounts[1]
    old_value = ["blahblah", addr, ["yesyesyes", "0x1234"]]
    tx = tester.setTuple(old_value)
    new_value = ["fooo", addr, ["nonono", "0x4321"]]
    tester.setTuple(new_value)

    with brownie.multicall(block_identifier=tx.block_number):
        assert tester.getTuple(addr) == old_value
    assert tester.getTuple(addr) == new_value


def test_all_values_come_from_the_same_block(chain, devnetwork):
    with brownie.multicall:
        first_call = brownie.multicall._contract.getBlockNumber()
        chain.mine(10)
        second_call = brownie.multicall._contract.getBlockNumber()
        assert first_call == second_call
        # pending calls have been flushed
        third_call = brownie.multicall._contract.getBlockNumber()
        chain.mine(10)
        fourth_call = brownie.multicall._contract.getBlockNumber()
        assert first_call == second_call == third_call == fourth_call

    assert brownie.multicall._contract.getBlockNumber() == first_call + 20
