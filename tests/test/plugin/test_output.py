#!/usr/bin/python3

import sys
from io import StringIO
from pathlib import Path

from brownie.test import output
from brownie.test.managers.runner import PytestPrinter

test_source = """
def test_stuff(BrownieTester, EVMTester, accounts):
    c = accounts[0].deploy(BrownieTester, True)
    print('oh hai', 'mark')
    c.doNothing({'from': accounts[0]})
    c.sendEth({'from': accounts[0]})
    d = accounts[0].deploy(EVMTester)
    d.modulusByZero(5, 1, {'from': accounts[0]})
    """


def test_print_gas(plugintester, mocker):
    mocker.spy(output, "_build_gas_profile_output")
    plugintester.runpytest("--gas")
    assert output._build_gas_profile_output.call_count == 1
    plugintester.runpytest()
    assert output._build_gas_profile_output.call_count == 1
    plugintester.runpytest("-G")
    assert output._build_gas_profile_output.call_count == 2


def test_print_coverage(plugintester, mocker):
    mocker.spy(output, "_build_coverage_output")
    plugintester.runpytest("--coverage")
    assert output._build_coverage_output.call_count == 1
    plugintester.runpytest()
    assert output._build_coverage_output.call_count == 1
    plugintester.runpytest("-C")
    assert output._build_coverage_output.call_count == 2


def test_coverage_save_report(plugintester):
    path = Path(plugintester.tmpdir).joinpath("reports")
    plugintester.runpytest()
    assert not len(list(path.glob("*")))
    plugintester.runpytest("-C")
    assert [i.name for i in path.glob("*")] == ["coverage.json"]
    plugintester.runpytest("-C")
    assert [i.name for i in path.glob("*")] == ["coverage.json"]
    next(path.glob("*")).open("w").write("this isn't json, is it?")
    plugintester.runpytest("-C")
    assert [i.name for i in path.glob("*")] == ["coverage.json"]


def test_stdout_capture(plugintester):
    result = plugintester.runpytest("-s")
    output = result.stdout.str()

    assert output.count("::test_stuff") == 2
    assert "oh hai mark" in output


def test_pytest_printer_uses_current_stdout(monkeypatch):
    first_stdout = StringIO()
    current_stdout = StringIO()
    monkeypatch.setattr(sys, "stdout", first_stdout)

    printer = PytestPrinter()
    printer.start()
    try:
        monkeypatch.setattr(sys, "stdout", current_stdout)
        print("oh hai", "mark")
    finally:
        printer.finish("tests/test_output.py::test_pytest_printer_uses_current_stdout")

    assert "oh hai mark" in current_stdout.getvalue()
    assert "oh hai mark" not in first_stdout.getvalue()
