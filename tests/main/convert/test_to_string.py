#!/usr/bin/python3

import pytest

from brownie.convert import to_string


def test_string():
    assert to_string("Hello!") == "Hello!"


def test_hexstring():
    assert to_string("0x48656c6c6f21") == "Hello!"


def test_hexstring_raise():
    with pytest.raises(ValueError):
        to_string("0xffff")
