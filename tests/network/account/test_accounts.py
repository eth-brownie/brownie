#!/usr/bin/python3
import pytest
from eip712.messages import EIP712Message, EIP712Type
from eth_account.datastructures import SignedMessage

from brownie.exceptions import UnknownAccount
from brownie.network.account import LocalAccount

priv_key = "0x416b8a7d9290502f5661da81f0cf43893e3d19cb9aea3c426cfb36e8186e9c09"
addr = "0x14b0Ed2a7C4cC60DD8F676AE44D0831d3c9b2a9E"


def test_repopulate(accounts, network, chain, rpc, network_name):
    assert len(accounts) > 0
    a = list(accounts)
    chain.reset()
    assert len(accounts) == len(a)
    for i in range(len(a)):
        assert a[i] == accounts[i]
    network.disconnect()
    assert len(accounts) == 0
    assert not rpc.is_active()
    network.connect(network_name)
    assert len(accounts) == len(a)


def test_contains(accounts):
    assert accounts[-1] in accounts
    assert str(accounts[-1]) in accounts
    assert "potato" not in accounts
    assert 12345 not in accounts


def test_add(devnetwork, accounts):
    assert len(accounts) == 10
    local = accounts.add()
    assert len(accounts) == 11
    assert type(local) is LocalAccount
    assert accounts[-1] == local
    accounts.add(priv_key)
    assert len(accounts) == 12
    assert accounts[-1].address == addr
    assert accounts[-1].private_key == priv_key
    accounts.add(priv_key)
    assert len(accounts) == 12


def test_at(accounts):
    with pytest.raises(UnknownAccount):
        accounts.at(addr)
    a = accounts.add(priv_key)
    assert a == accounts.at(addr)
    assert a == accounts.at(a)
    accounts._reset()


def test_remove(accounts):
    assert len(accounts) == 10
    with pytest.raises(UnknownAccount):
        accounts.remove(addr)
    a = accounts.add(priv_key)
    accounts.remove(a)
    with pytest.raises(UnknownAccount):
        accounts.remove(a)
    accounts.add(priv_key)
    accounts.remove(addr)
    accounts.add(priv_key)
    accounts.remove(addr.lower())
    accounts._reset()


def test_clear(accounts):
    assert len(accounts) == 10
    accounts.clear()
    assert len(accounts) == 0
    accounts._reset()


def test_delete(accounts):
    assert len(accounts) == 10
    a = accounts[-1]
    del accounts[-1]
    assert len(accounts) == 9
    assert a not in accounts


def test_default_remains_after_reset(accounts):
    accounts.default = accounts[0]
    accounts._reset()
    assert accounts.default == accounts[0]


def test_default_cleared_on_disconnect(accounts, network):
    accounts.default = accounts[0]
    network.disconnect()
    assert accounts.default is None


def test_from_mnemonic(accounts):
    acct = accounts.from_mnemonic(
        "street dutch license offer where music rice correct stomach there right surprise"
    )

    assert isinstance(acct, LocalAccount)
    assert acct.address == "0x64483769Cd246aa69956B18bfd49F20426FdE2A6"


def test_mnemonic_multiple(accounts):
    acct = accounts.from_mnemonic(
        "grant buyer family hybrid recipe motor cube general apart snow monster tunnel", 3
    )
    assert [str(i) for i in acct] == [
        "0x4d44087e86DaEA4db7030F0558D083a75114F56C",
        "0xD57D53eCEFAA99b9f1d67a8C4D21E46fC16Aa133",
        "0x0efE90a99343A9AcF48501FAF3505b10822067c6",
    ]


def test_mnemonic_offset(accounts):
    acct = accounts.from_mnemonic(
        "retire basic saddle brief bridge path cradle credit angry vendor repair rhythm", offset=5
    )

    assert acct.address == "0x12ba8F2E54B1B57C54D1CA06c0a0b8d14E9abc62"


def test_mnemonic_offset_multiple(accounts):
    acct = accounts.from_mnemonic(
        "day axis gallery size rebuild logic steak food palm victory useful kick", 2, 7
    )
    assert [str(i) for i in acct] == [
        "0x44302d4c1e535b4FB77bc390e3053586ecA411b0",
        "0x1F413d7E7B85E557D9997E6714479C7848A9Ea07",
    ]


def test_sign_message(accounts):
    class TestSubType(EIP712Type):
        inner: "uint256"  # type: ignore # noqa: F821

    class TestMessage(EIP712Message):
        _name_: "string" = "Brownie Tests"  # type: ignore # noqa: F821
        value: "uint256"  # type: ignore # noqa: F821
        default_value: "address" = "0xFFfFfFffFFfffFFfFFfFFFFFffFFFffffFfFFFfF"  # type: ignore # noqa: F821,E501
        sub: TestSubType

    local = accounts.add(priv_key)
    msg = TestMessage(value=1, sub=TestSubType(inner=2))
    signed = local.sign_message(msg)
    assert isinstance(signed, SignedMessage)
    assert (
        signed.messageHash.hex()
        == "0x131c497d4b815213752a2a00564dcf667c3bf3f85a410ef8cb50050b51959c26"
    )


def test_sign_defunct_message(accounts):
    local = accounts.add(priv_key)
    msg = f"I authorize Foundation to migrate my account to {local.address.lower()}"
    signed = local.sign_defunct_message(msg)
    assert (
        signed.messageHash.hex()
        == "0xb9bb14ce5c17b2b7217cfa638031a542b95fc25b18d42a61409066001d01351d"
    )


def test_force_unlock(accounts):
    acct = accounts.at("0x0000000000000000000000000000000000001337", True)
    accounts[0].transfer(acct, "1 ether")
    acct.transfer(accounts[0], "0.4 ether")

    assert acct.nonce == 1
    assert acct.balance() == "0.6 ether"
