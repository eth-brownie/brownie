#!/usr/bin/python3

from brownie.types.convert import wei


def test_nonetype():
    assert wei(None) == 0


def test_bytes():
    assert wei(b'\xff') == 255


def test_scientific_notation():
    assert wei(8.32e26) == 832000000000000000000000000


def test_float():
    assert wei(1.99) == 1


def test_int():
    assert wei(1000) == 1000


def test_str():
    assert wei("1000") == 1000


def test_hexstr():
    assert wei("0xff") == 255


def test_string_with_unit():
    assert wei("3.66 ether") == 3660000000000000000
    assert wei("89.006 gwei") == 89006000000
