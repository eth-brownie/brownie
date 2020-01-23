#!/usr/bin/python3

import pytest

from brownie.convert.normalize import format_input

abi = {
    "inputs": [
        {"name": "fixedArray", "type": "uint16[3]"},
        {"name": "dynamicArray", "type": "uint8[]"},
        {"name": "nestedArray", "type": "uint32[2][]"},
        {"name": "simple", "type": "bytes32"},
    ],
    "name": "testFunction",
}


def test_empty():
    with pytest.raises(TypeError):
        format_input({"inputs": [], "name": "empty"}, [1])


def test_success():
    assert format_input(abi, [(1, 2, 3), (1,), ([1, 1], [2, 2]), "0xff"])


def test_wrong_length_initial():
    with pytest.raises(ValueError):
        format_input(abi, [(1, 2, 3), (1,), ([1, 1], [2, 2])])
    with pytest.raises(ValueError):
        format_input(abi, [(1, 2, 3), (1,), ([1, 1], [2, 2]), "0xff", "0xff"])


def test_wrong_length_fixed_array():
    with pytest.raises(ValueError):
        format_input(abi, [(1, 2), (2,), ([2, 2], [2, 2]), "0xff"])


def test_wrong_length_nested_array():
    with pytest.raises(ValueError):
        format_input(abi, [(1, 2, 3), (2,), ([2, 2, 2], [2, 2, 2]), "0xff"])


def test_non_sequence():
    with pytest.raises(TypeError):
        format_input(abi, ["123", (1,), ([1, 1], [2, 2]), "0xff"])
