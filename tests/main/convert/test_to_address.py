#!/usr/bin/python3

import pytest

from brownie.convert import to_address

addr = "0x14b0Ed2a7C4cC60DD8F676AE44D0831d3c9b2a9E"
addr_encoded = b"\x14\xb0\xed*|L\xc6\r\xd8\xf6v\xaeD\xd0\x83\x1d<\x9b*\x9e"


def test_success():
    assert to_address(addr) == addr
    assert to_address(addr.lower()) == addr
    assert to_address(addr.upper()) == addr
    assert to_address(addr[2:]) == addr


def test_bytes_success():
    assert to_address(addr_encoded) == addr


def test_wrong_length():
    with pytest.raises(ValueError):
        to_address("0x00")
    with pytest.raises(ValueError):
        to_address(addr[:20])
    with pytest.raises(ValueError):
        to_address(addr + "00")
