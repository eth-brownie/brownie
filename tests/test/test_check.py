#!/usr/bin/python3

import pytest

from brownie import accounts, check
from brownie.network.transaction import TransactionReceipt


def test_true():
    check.true(True)
    with pytest.raises(AssertionError):
        check.true(1)
    with pytest.raises(AssertionError):
        check.true(False)


def test_false():
    check.false(False)
    with pytest.raises(AssertionError):
        check.false(0)
    with pytest.raises(AssertionError):
        check.false(True)


def test_confirms(token):
    tx = check.confirms(token.transfer, (accounts[1], 1000, {'from': accounts[0]}))
    assert type(tx) is TransactionReceipt
    with pytest.raises(AssertionError):
        check.confirms(token.transfer, (accounts[1], 1000, {'from': accounts[8]}))


def test_reverts(tester):
    check.reverts(tester.testRevertStrings, (0, {'from': accounts[0]}))
    check.reverts(tester.testRevertStrings, (0, {'from': accounts[0]}), "zero")
    check.reverts(tester.testRevertStrings, (1, {'from': accounts[0]}), "dev: one")
    with pytest.raises(AssertionError):
        check.reverts(tester.testRevertStrings, (5, {'from': accounts[0]}))
    with pytest.raises(AssertionError):
        check.reverts(tester.testRevertStrings, (1, {'from': accounts[0]}), "oops")


def test_event_fired(tester):
    tx = tester.testRevertStrings(5, {'from': accounts[0]})
    check.event_fired(tx, "Debug")
    check.event_fired(tx, "Debug", 1)
    check.event_fired(tx, "Debug", 1, {'a': 5})
    check.event_fired(tx, "Debug", 1, [{'a': 5}])
    check.event_fired(tx, "Debug", values={'a': 5})
    with pytest.raises(TypeError):
        check.event_fired(tx, "Debug", 1, 5)
    with pytest.raises(ValueError):
        check.event_fired(tx, "Debug", 1, [{'a': 5}, {'a': 4}])
    with pytest.raises(AssertionError):
        check.event_fired(tx, "Debug", 2)
    with pytest.raises(AssertionError):
        check.event_fired(tx, "NotAnEvent")
    with pytest.raises(AssertionError):
        check.event_fired(tx, "Debug", 1, {'a': 6})
    with pytest.raises(AssertionError):
        check.event_fired(tx, "Debug", 1, {'b': 5})


def test_event_not_fired(tester):
    tx = tester.testRevertStrings(5, {'from': accounts[0]})
    check.event_not_fired(tx, "NotAnEvent")
    with pytest.raises(AssertionError):
        check.event_not_fired(tx, "Debug")


NOT_EQUAL = [
    (True, 1, "1"),
    (False, None, 0, "0", "0x00"),
    ("0x", 0)
]

EQ_NOT_STRICT = [
    (1000, 1000.0, "1 kwei"),
    ("0xf", "0xF", "0x0000f", "0x00000000f")
]


def test_equal():
    for strict in (True, False):
        check.equal({1: 2}, {1: 2}, strict=strict)
        check.equal([{1: 2}], [{1: 2}], strict=strict)
        check.equal([1, 2, 3], (1, 2, 3), strict=strict)
        with pytest.raises(AssertionError):
            check.equal([1, 1], [1, 1, 1], strict=strict)
    for row in EQ_NOT_STRICT:
        for a, b in [(i, x) for i in row for x in row if x is not i]:
            check.equal(a, b)
            with pytest.raises(AssertionError):
                check.equal(a, b, strict=True)
        for i in range(1, len(row)):
            check.equal(row[:i], row[-i:])
            with pytest.raises(AssertionError):
                check.equal(row[:i], row[-i:], strict=True)
    for row in NOT_EQUAL:
        for a, b in [(i, x) for i in row for x in row if x is not i]:
            with pytest.raises(AssertionError):
                check.equal(a, b)
            with pytest.raises(AssertionError):
                check.equal(a, b, strict=True)


def test_not_equal():
    for strict in (True, False):
        with pytest.raises(AssertionError):
            check.not_equal({1: 2}, {1: 2}, strict=strict)
        with pytest.raises(AssertionError):
            check.not_equal([{1: 2}], [{1: 2}], strict=strict)
        with pytest.raises(AssertionError):
            check.not_equal([1, 2, 3], (1, 2, 3), strict=strict)
        check.not_equal([1, 1], [1, 1, 1], strict=strict)
    for row in EQ_NOT_STRICT:
        for a, b in [(i, x) for i in row for x in row if x is not i]:
            with pytest.raises(AssertionError):
                check.not_equal(a, b)
            check.not_equal(a, b, strict=True)
        for i in range(1, len(row)):
            with pytest.raises(AssertionError):
                check.not_equal(row[:i], row[-i:])
            check.not_equal(row[:i], row[-i:], strict=True)
    for row in NOT_EQUAL:
        for a, b in [(i, x) for i in row for x in row if x is not i]:
            check.not_equal(a, b)
            check.not_equal(a, b, strict=True)


def test_check_equal_accounts():
    check.equal(accounts[0], accounts[0].address)
    check.equal(accounts[0].address, accounts[0])
    check.not_equal(accounts[0], accounts[1])
    a = accounts.add("0x125192be77a29090a29cbcd20c86d2d0b52aea30bc5cbb1e3262cf96682d0d2e")
    check.equal(a, "0x0f4fB750E15592489F0CFf7C287AA74563c71Cae")
    check.equal("0x0f4fB750E15592489F0CFf7C287AA74563c71Cae", a)
    check.not_equal(a, accounts[0])
    check.not_equal(a, accounts.add())
