import inspect

import pytest
from lazy_object_proxy import Proxy

import brownie
from brownie.exceptions import ContractNotFound


def test_auto_deploy_on_testnet(config, devnetwork):
    with brownie.Multicall():
        # gets deployed on init
        assert "multicall2" in config.active_network
        addr = config.active_network["multicall2"]

    with brownie.Multicall():
        # uses the previously deployed instance
        assert config.active_network["multicall2"] == addr


def test_proxy_object_is_returned_from_calls(accounts, tester):
    addr = accounts[1]
    value = ["blahblah", addr, ["yesyesyes", "0x1234"]]
    tester.setTuple(value)

    with brownie.Multicall() as m:
        # the value hasn't been fetched so ret_value is just the proxy
        # but if we access ret_val again it will update
        # so use getattr_static to see it has yet to update
        ret_val = tester.getTuple(addr, {"from": m})
        assert inspect.getattr_static(ret_val, "__wrapped__") != value
        assert isinstance(ret_val, Proxy)
        assert ret_val.__wrapped__ == value


def test_flush_mid_execution(accounts, tester):
    addr = accounts[1]
    value = ["blahblah", addr, ["yesyesyes", "0x1234"]]
    tester.setTuple(value)

    with brownie.Multicall() as m:
        tester.getTuple(addr, {"from": m})
        assert len(m._pending_calls) == 1
        m.flush()
        assert len(m._pending_calls) == 0


def test_proxy_object_fetches_on_next_use(accounts, tester):
    addr = accounts[1]
    value = ["blahblah", addr, ["yesyesyes", "0x1234"]]
    tester.setTuple(value)

    with brownie.Multicall() as m:
        ret_val = tester.getTuple(addr, {"from": m})
        assert len(m._pending_calls) == 1
        # ret_val is now fetched
        assert ret_val == value
        assert len(m._pending_calls) == 0


def test_proxy_object_updates_on_exit(accounts, tester):
    addr = accounts[1]
    value = ["blahblah", addr, ["yesyesyes", "0x1234"]]
    tester.setTuple(value)

    with brownie.Multicall() as m:
        ret_val = tester.getTuple(addr, {"from": m})

    assert ret_val == value


def test_standard_calls_passthrough(accounts, tester):
    addr = accounts[1]
    value = ["blahblah", addr, ["yesyesyes", "0x1234"]]
    tester.setTuple(value)

    with brownie.Multicall():
        assert tester.getTuple(addr) == value


def test_standard_calls_work_after_context(accounts, tester):
    addr = accounts[1]
    value = ["blahblah", addr, ["yesyesyes", "0x1234"]]
    tester.setTuple(value)

    with brownie.Multicall():
        assert tester.getTuple(addr) == value

    assert tester.getTuple(addr) == value


def test_double_multicall(accounts, tester):
    addr = accounts[1]
    value = ["blahblah", addr, ["yesyesyes", "0x1234"]]
    tester.setTuple(value)

    with brownie.Multicall() as mc1:
        tester.getTuple(addr, {"from": mc1})
        with brownie.Multicall() as mc2:
            mc2._contract.getCurrentBlockTimestamp({"from": mc2})
            assert len(mc1._pending_calls) == 1
            assert len(mc2._pending_calls) == 1
        assert len(mc1._pending_calls) == 1
        assert len(mc2._pending_calls) == 0


def test_raises_for_ancient_block_identifier(accounts, tester):
    addr = accounts[1]
    value = ["blahblah", addr, ["yesyesyes", "0x1234"]]
    tx = tester.setTuple(value)

    with pytest.raises(ContractNotFound):
        # block identifier is before multicall existed
        with brownie.Multicall(block_identifier=tx.block_number):
            pass


def test_deploy_classmethod(accounts, config):
    multicall = brownie.Multicall.deploy({"from": accounts[0]})
    assert config.active_network["multicall2"] == multicall.address


def test_using_block_identifier(accounts, tester):
    # need to deploy before progressing chain
    brownie.Multicall.deploy({"from": accounts[0]})

    addr = accounts[1]
    old_value = ["blahblah", addr, ["yesyesyes", "0x1234"]]
    tx = tester.setTuple(old_value)
    new_value = ["fooo", addr, ["nonono", "0x4321"]]
    tester.setTuple(new_value)

    with brownie.Multicall(block_identifier=tx.block_number) as m:
        assert tester.getTuple(addr, {"from": m}) == old_value
    assert tester.getTuple(addr) == new_value


def test_all_values_come_from_the_same_block(chain, devnetwork):
    with brownie.Multicall() as m:
        first_call = m._contract.getBlockNumber({"from": m})
        chain.mine(10)
        second_call = m._contract.getBlockNumber({"from": m})
        assert first_call == second_call
        # pending calls have been flushed
        third_call = m._contract.getBlockNumber({"from": m})
        chain.mine(10)
        fourth_call = m._contract.getBlockNumber({"from": m})
        assert first_call == second_call == third_call == fourth_call

    assert m._contract.getBlockNumber() == first_call + 20
