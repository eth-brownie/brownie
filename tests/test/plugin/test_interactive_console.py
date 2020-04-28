#!/usr/bin/python3

test_source = """
def test_that_fails():
    assert False

def test_that_also_fails():
    assert False
    """


def test_interact(plugintester, mocker, monkeypatch, console):

    monkeypatch.setattr("brownie._cli.console.Console.__init__", lambda *args, **kwargs: None)
    monkeypatch.setattr("brownie._cli.console.Console.interact", lambda *args, **kwargs: None)
    mocker.spy(console, "interact")

    plugintester.runpytest()
    assert not console.interact.call_count

    plugintester.runpytest("--interactive")
    assert console.interact.call_count == 2
