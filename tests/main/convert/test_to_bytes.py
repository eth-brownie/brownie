#!/usr/bin/python3

import pytest

from brownie.convert import to_bytes


def test_type_bounds():
    with pytest.raises(ValueError):
        to_bytes("0x00", "bytes0")
    with pytest.raises(ValueError):
        to_bytes("0x00", "bytes33")


def test_length_bounds():
    for i in range(1, 33):
        type_ = "bytes" + str(i)
        to_bytes("0x" + "ff" * i, type_)
        with pytest.raises(OverflowError):
            to_bytes("0x" + "ff" * (i + 1), type_)


def test_string_raises():
    with pytest.raises(ValueError):
        to_bytes("abcdefg")


def test_hexstring():
    assert to_bytes("0xffff", "bytes") == b"\xff\xff"
    assert to_bytes("0xffff", "bytes2") == b"\xff\xff"
    assert to_bytes("0xffff", "bytes4") == b"\x00\x00\xff\xff"
    assert to_bytes("abcdef")


def test_left_pad():
    for i in range(1, 33):
        type_ = "bytes" + str(i)
        assert to_bytes("0xff", type_).hex() == (i - 1) * "00" + "ff"


def test_int_bounds():
    for i in range(1, 33):
        type_ = "bytes" + str(i)
        assert to_bytes(2 ** (i * 8) - 1, type_).hex() == "ff" * i
        with pytest.raises(OverflowError):
            to_bytes(2 ** (i * 8), type_)


def test_byte_is_bytes1():
    assert to_bytes(42, "byte") == to_bytes(42, "bytes1")


def test_zero_value():
    assert to_bytes("", "bytes1").hex() == "00"
    assert to_bytes("0x", "bytes1").hex() == "00"
    assert to_bytes(0, "bytes1").hex() == "00"


def test_invalid_type():
    with pytest.raises(TypeError):
        to_bytes(None)
    with pytest.raises(TypeError):
        to_bytes(3.1337)
    with pytest.raises(TypeError):
        to_bytes(True)
