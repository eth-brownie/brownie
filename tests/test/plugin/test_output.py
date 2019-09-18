#!/usr/bin/python3

from pathlib import Path

from brownie.test import output

test_source = """
def test_stuff(BrownieTester, accounts):
    c = accounts[0].deploy(BrownieTester, True)
    c.doNothing({'from': accounts[0]})"""


def test_print_gas(plugintester, mocker):
    mocker.spy(output, "_print_gas_profile")
    plugintester.runpytest("--gas")
    assert output._print_gas_profile.call_count == 1
    plugintester.runpytest()
    assert output._print_gas_profile.call_count == 1
    plugintester.runpytest("-G")
    assert output._print_gas_profile.call_count == 2


def test_print_coverage(plugintester, mocker):
    mocker.spy(output, "_print_coverage_totals")
    plugintester.runpytest("--coverage")
    assert output._print_coverage_totals.call_count == 1
    plugintester.runpytest()
    assert output._print_coverage_totals.call_count == 1
    plugintester.runpytest("-C")
    assert output._print_coverage_totals.call_count == 2


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
