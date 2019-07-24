#!/usr/bin/python3

import pytest
import sys

from brownie.cli.utils import color


class Win32:

    def __init__(self):
        self.platform = sys.platform
        self.on()

    def on(self):
        sys.platform = "win32"

    def off(self):
        sys.platform = self.platform


@pytest.fixture(scope="function")
def win32():
    w = Win32()
    yield w
    w.off()


@pytest.mark.skipif('sys.platform == "win32"')
def test_no_colors_on_windows(win32):
    a = color('error')
    assert not a
    win32.off()
    assert a != color('error')


@pytest.mark.skipif('sys.platform == "win32"')
def test_call_getitem(win32):
    assert color('success') == color['success'] == ""
    assert str(color) == ""
    win32.off()
    assert color('success') == color['success'] != ""
    assert str(color) == "\x1b[0;m"


@pytest.mark.skipif('sys.platform == "win32"')
def test_bright_dark():
    assert color('yellow') != color('dark yellow') != color('bright yellow') != ""


def test_pretty_dict(win32):
    x = {1: 2, "foo": "bar", "baz": True}
    assert x == eval(color.pretty_dict(x))
    x = {'foo': [1, 2], 'bar': ["a", "b", "c"]}
    assert x == eval(color.pretty_dict(x))
    x = {'yes': {'maybe': 1, 'no': 2}, 'no': {1: 2, 4: True}}
    assert x == eval(color.pretty_dict(x))


def test_pretty_list(win32):
    x = [1, 2, 3, 4, 5]
    assert x == eval(color.pretty_list(x))
    x = (1, 2, 3, 4, 5)
    assert x == eval(color.pretty_list(x))
    x = [{'foo': "bar"}, {'potato': 123}]
    assert x == eval(color.pretty_list(x))
    x = [
        "0000000100000000000000000000000000000000000000000000000000000000",
        "0000000100000000000000000000000000000000000000000000000000000000",
        "0000000100000000000000000000000000000000000000000000000000000000"
    ]
    assert x == eval(color.pretty_list(x))


def test_format_tb():
    try:
        raise NameError("You dun goofed now")
    except Exception:
        x = color.format_tb(sys.exc_info())
        assert x
        assert x != color.format_tb(sys.exc_info(), start=1)
