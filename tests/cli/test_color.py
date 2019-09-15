#!/usr/bin/python3

import pytest
import sys

from brownie.cli.utils import color


@pytest.fixture
def colorpatch(monkeypatch):
    def patched(*args):
        return ""

    monkeypatch.setattr("brownie.cli.utils.Color.__call__", patched)
    monkeypatch.setattr("brownie.cli.utils.Color.__getitem__", patched)
    monkeypatch.setattr("brownie.cli.utils.Color.__str__", patched)
    yield


def test_call_getitem():
    assert color("success") == color["success"] != ""
    assert str(color) == "\x1b[0;m"


def test_bright_dark():
    assert color("yellow") != color("dark yellow") != color("bright yellow") != ""


def test_pretty_dict(colorpatch):
    x = {1: 2, "foo": "bar", "baz": True}
    assert x == eval(color.pretty_dict(x))
    x = {"foo": [1, 2], "bar": ["a", "b", "c"]}
    assert x == eval(color.pretty_dict(x))
    x = {"yes": {"maybe": 1, "no": 2}, "no": {1: 2, 4: True}}
    assert x == eval(color.pretty_dict(x))


def test_pretty_list(colorpatch):
    x = [1, 2, 3, 4, 5]
    assert x == eval(color.pretty_list(x))
    x = (1, 2, 3, 4, 5)
    assert x == eval(color.pretty_list(x))
    x = [{"foo": "bar"}, {"potato": 123}]
    assert x == eval(color.pretty_list(x))
    x = [
        "0000000100000000000000000000000000000000000000000000000000000000",
        "0000000100000000000000000000000000000000000000000000000000000000",
        "0000000100000000000000000000000000000000000000000000000000000000",
    ]
    assert x == eval(color.pretty_list(x))


def test_format_tb():
    try:
        raise NameError("You dun goofed now")
    except Exception:
        x = color.format_tb(sys.exc_info())
        assert x
        assert x != color.format_tb(sys.exc_info(), start=1)
