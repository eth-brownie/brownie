#!/usr/bin/python3

import pytest

from brownie.types.convert import to_bytes


def test_type_bounds():
    with pytest.raises(ValueError):
        to_bytes("0x00", "bytes0")
    with pytest.raises(ValueError):
        to_bytes("0x", "bytes33")


def test_length_bounds():
    for i in range(1, 33):
        type_ = "bytes"+str(i)
        to_bytes("0x"+"ff"*i, type_)
        with pytest.raises(OverflowError):
            to_bytes("0x"+"ff"*(i+1), type_)


def test_string_raises():
    with pytest.raises(TypeError):
        to_bytes("abcdefg")


def test_hexstring():
    assert to_bytes("0xffff", "bytes") == b'\xff\xff'
    assert to_bytes("0xffff", "bytes2") == b'\xff\xff'
    assert to_bytes("0xffff", "bytes4") == b'\x00\x00\xff\xff'


def test_left_pad():
    for i in range(1, 33):
        type_ = "bytes"+str(i)
        assert to_bytes("0xff", type_).hex() == (i-1)*"00"+"ff"


def test_int_bounds():
    for i in range(1, 33):
        type_ = "bytes"+str(i)
        assert to_bytes(2**(i*8)-1, type_).hex() == "ff"*i
        with pytest.raises(OverflowError):
            to_bytes(2**(i*8), type_)
