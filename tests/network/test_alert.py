#!/usr/bin/python3

import time

import pytest

from brownie import alert


class AlertTest:
    def __init__(self, initial_value, args=tuple(), kwargs={}):
        self.value = [initial_value]
        self.args = args
        self.kwargs = kwargs
        self.raised = False

    def __call__(self, *args, **kwargs):
        if args != self.args or kwargs != self.kwargs:
            self.raised = True
            raise ValueError
        return self.value[-1]

    def set_value(self, value):
        self.value = [self.value[-1], value]

    def callback(self, old, new):
        if self.value != [old, new]:
            self.raised = True


@pytest.fixture(scope="function", autouse=True)
def setup():
    yield
    alert.stop_all()


def _alert_fn():
    return True


def test_raises():
    with pytest.raises(TypeError):
        alert.new("foo")
    assert len(alert.show()) == 0
    with pytest.raises(ValueError):
        alert.new(time.time, repeat=-1)
    assert len(alert.show()) == 0
    with pytest.raises(TypeError):
        alert.new(time.time, args=("potato",))
    assert len(alert.show()) == 0


def test_new():
    a = alert.new(_alert_fn, delay=0.1)
    assert type(a) is alert.Alert
    assert alert.show() == [a]
    b = alert.Alert(_alert_fn, delay=0.1)
    assert a != b
    assert len(alert.show()) == 2


def test_show():
    a = alert.new(_alert_fn, delay=0.1)
    time.sleep(0.05)
    b = alert.new(_alert_fn, delay=0.1)
    time.sleep(0.05)
    c = alert.new(_alert_fn, delay=0.1)
    assert alert.show() == [a, b, c]


def test_stop():
    alert.new(_alert_fn, delay=0.1)
    a = alert.new(_alert_fn, delay=0.1)
    assert len(alert.show()) == 2
    a.stop(False)
    a.wait()
    assert len(alert.show()) == 1
    alert.new(_alert_fn, delay=0.1)
    alert.new(_alert_fn, delay=0.1)
    assert len(alert.show()) == 3
    alert.stop_all()
    assert len(alert.show()) == 0


def test_fire_msg(capfd):
    t = AlertTest(False)
    alert.new(t, delay=0.03, msg="Fired")
    assert not capfd.readouterr()[0].strip()
    t.set_value(True)
    time.sleep(0.08)
    assert capfd.readouterr()[0].strip()[-5:] == "Fired"
    assert len(alert.show()) == 0


def test_fire_callback(capfd):
    t = AlertTest("foo")
    alert.new(t, delay=0.01, callback=t.callback)
    time.sleep(0.03)
    assert not t.raised
    assert len(alert.show()) == 1
    t.set_value("bar")
    time.sleep(0.03)
    assert not t.raised
    assert len(alert.show()) == 0


def test_args_kwargs():
    t = AlertTest(False, (1, 2, 3), {"foo": "bar"})
    alert.new(t, (1, 2, 3), {"foo": "bar"}, delay=0.01)
    time.sleep(0.02)
    assert not t.raised
    assert len(alert.show()) == 1


def test_repeat():
    t = AlertTest("foo")
    a = alert.new(t, delay=0.01, callback=t.callback, repeat=2)
    time.sleep(0.05)
    assert not t.raised
    assert len(alert.show()) == 1
    t.set_value("bar")
    time.sleep(0.05)
    assert not t.raised
    assert len(alert.show()) == 1
    t.set_value("foo")
    time.sleep(0.05)
    assert not t.raised
    assert a.is_alive()
    assert len(alert.show()) == 1
    t.set_value("potato")
    time.sleep(0.05)
    assert not t.raised
    assert not a.is_alive()
    assert len(alert.show()) == 0
