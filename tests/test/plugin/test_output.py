#!/usr/bin/python3

from pathlib import Path
from brownie.test import output

test_source = '''
def test_stuff(Token, accounts):
    token = accounts[0].deploy(Token, "Test Token", "TST", 18, "1000 ether")
    token.transfer(accounts[1], "10 ether", {'from': accounts[0]})'''


def test_print_gas(plugintester, mocker):
    mocker.spy(output, 'print_gas_profile')
    plugintester.runpytest('--gas')
    assert output.print_gas_profile.call_count == 1
    plugintester.runpytest()
    assert output.print_gas_profile.call_count == 1
    plugintester.runpytest('-G')
    assert output.print_gas_profile.call_count == 2


def test_print_coverage(plugintester, mocker):
    mocker.spy(output, 'print_coverage_totals')
    plugintester.runpytest('--coverage')
    assert output.print_coverage_totals.call_count == 1
    plugintester.runpytest()
    assert output.print_coverage_totals.call_count == 1
    plugintester.runpytest('-C')
    assert output.print_coverage_totals.call_count == 2


def test_coverage_save_report(plugintester):
    path = Path(plugintester.tmpdir).joinpath('reports')
    plugintester.runpytest()
    assert not len(list(path.glob('*')))
    plugintester.runpytest('-C')
    assert len(list(path.glob('*'))) == 1
    plugintester.runpytest('-C')
    assert len(list(path.glob('*'))) == 1
    next(path.glob('*')).open('w').write("this isn't json, is it?")
    plugintester.runpytest('-C')
    assert len(list(path.glob('*'))) == 2
