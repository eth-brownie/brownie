#!/usr/bin/python3

import pytest

from brownie.types.convert import to_bool


def test_success_bool():
    assert to_bool(True) is True
    assert to_bool(False) is False


def test_success_float():
    assert to_bool(1.0) is True
    assert to_bool(0.0) is False


def test_fail_float():
    with pytest.raises(TypeError):
        to_bool(1.23)
    with pytest.raises(TypeError):
        to_bool(0.9)
    with pytest.raises(TypeError):
        to_bool(-1.0)


def test_success_int():
    assert to_bool(1) is True
    assert to_bool(0) is False


def test_fail_int():
    with pytest.raises(TypeError):
        to_bool(2)
    with pytest.raises(TypeError):
        to_bool(-1)


def test_fail_nonetype():
    with pytest.raises(TypeError):
        to_bool(None)


def test_fail_str():
    with pytest.raises(TypeError):
        to_bool("1")


def test_fail_list():
    with pytest.raises(TypeError):
        to_bool([])


def test_fail_dict():
    with pytest.raises(TypeError):
        to_bool({})
