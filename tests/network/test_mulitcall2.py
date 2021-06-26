import inspect

from lazy_object_proxy import Proxy

import brownie


def test_auto_deploy_on_testnet(config, devnetwork):
    with brownie.multicall2():
        # gets deployed on init
        assert "multicall2" in config.active_network
        addr = config.active_network["multicall2"]

    with brownie.multicall2():
        # uses the previously deployed instance
        assert config.active_network["multicall2"] == addr


def test_proxy_object_is_returned_from_calls(accounts, tester):
    addr = accounts[1]
    value = ["blahblah", addr, ["yesyesyes", "0x1234"]]
    tester.setTuple(value)

    with brownie.multicall2() as mc2:
        # the value hasn't been fetched so ret_value is just the proxy
        # but if we access ret_val again it will update
        # so use getattr_static to see it has yet to update
        ret_val = tester.getTuple(addr, {"from": mc2})
        assert inspect.getattr_static(ret_val, "__wrapped__") != value
        assert isinstance(ret_val, Proxy)
        assert ret_val.__wrapped__ == value


def test_flush_mid_execution(accounts, tester):
    addr = accounts[1]
    value = ["blahblah", addr, ["yesyesyes", "0x1234"]]
    tester.setTuple(value)

    with brownie.multicall2() as mc2:
        tester.getTuple(addr, {"from": mc2})
        assert len(mc2._pending_calls) == 1
        mc2.flush()
        assert len(mc2._pending_calls) == 0


def test_proxy_object_fetches_on_next_use(accounts, tester):
    addr = accounts[1]
    value = ["blahblah", addr, ["yesyesyes", "0x1234"]]
    tester.setTuple(value)

    with brownie.multicall2() as mc2:
        ret_val = tester.getTuple(addr, {"from": mc2})
        assert len(mc2._pending_calls) == 1
        # ret_val is now fetched
        assert ret_val == value
        assert len(mc2._pending_calls) == 0


def test_proxy_object_updates_on_exit(accounts, tester):
    addr = accounts[1]
    value = ["blahblah", addr, ["yesyesyes", "0x1234"]]
    tester.setTuple(value)

    with brownie.multicall2() as mc2:
        ret_val = tester.getTuple(addr, {"from": mc2})

    assert ret_val == value


def test_standard_calls_passthrough(accounts, tester):
    addr = accounts[1]
    value = ["blahblah", addr, ["yesyesyes", "0x1234"]]
    tester.setTuple(value)

    with brownie.multicall2():
        assert tester.getTuple(addr) == value


def test_standard_calls_work_after_context(accounts, tester):
    addr = accounts[1]
    value = ["blahblah", addr, ["yesyesyes", "0x1234"]]
    tester.setTuple(value)

    with brownie.multicall2():
        assert tester.getTuple(addr) == value

    assert tester.getTuple(addr) == value


def test_double_multicall(accounts, tester):
    addr = accounts[1]
    value = ["blahblah", addr, ["yesyesyes", "0x1234"]]
    tester.setTuple(value)

    with brownie.multicall2() as mc1:
        tester.getTuple(addr, {"from": mc1})
        with brownie.multicall2() as mc2:
            mc2._contract.getCurrentBlockTimestamp({"from": mc2})
            assert len(mc1._pending_calls) == 1
            assert len(mc2._pending_calls) == 1
        assert len(mc1._pending_calls) == 1
        assert len(mc2._pending_calls) == 0
