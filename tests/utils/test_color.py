#!/usr/bin/python3

import pytest

from brownie.utils import color


@pytest.fixture
def colorpatch(monkeypatch):
    def patched(*args):
        return ""

    monkeypatch.setattr("brownie.utils.Color.__call__", patched)
    monkeypatch.setattr("brownie.utils.Color.__str__", patched)
    yield


def test_call():
    assert color("red") != ""
    assert str(color) == "\x1b[0;m"


def test_unknown():
    assert color("potato") == color()


def test_bright_dark():
    assert color("yellow") != color("dark yellow") != color("bright yellow") != ""


def test_pretty_dict(colorpatch):
    x = {1: 2, "foo": "bar", "baz": True}
    assert x == eval(color.pretty_dict(x))
    x = {"foo": [1, 2], "bar": ["a", "b", "c"]}
    assert x == eval(color.pretty_dict(x))
    x = {"yes": {"maybe": 1, "no": 2}, "no": {1: 2, 4: True}}
    assert x == eval(color.pretty_dict(x))


def test_pretty_sequence(colorpatch):
    x = [1, 2, 3, 4, 5]
    assert x == eval(color.pretty_sequence(x))
    x = (1, 2, 3, 4, 5)
    assert x == eval(color.pretty_sequence(x))
    x = [{"foo": "bar"}, {"potato": 123}]
    assert x == eval(color.pretty_sequence(x))
    x = [
        "0000000100000000000000000000000000000000000000000000000000000000",
        "0000000100000000000000000000000000000000000000000000000000000000",
        "0000000100000000000000000000000000000000000000000000000000000000",
    ]
    assert x == eval(color.pretty_sequence(x))


def test_format_tb():
    try:
        # by raising, the exception has a traceback
        raise NameError("You dun goofed now")
    except Exception as exc:
        x = color.format_tb(exc)
        assert x
        assert x != color.format_tb(exc, start=1)


def test_show_colors_config(config):
    config.settings["console"]["show_colors"] = False
    assert color("blue") == ""
