#!/usr/bin/python3

from pathlib import Path

test_source = '''
def test_stuff(Token, accounts):
    token = accounts[0].deploy(Token, "Test Token", "TST", 18, "1000 ether")
    token.transfer(accounts[1], "10 ether", {'from': accounts[0]})'''


def test_print_gas(testdir, methodwatch):
    methodwatch.watch('brownie.test.output.print_gas_profile')
    testdir.runpytest('--gas')
    methodwatch.assert_called()
    methodwatch.reset()
    testdir.runpytest()
    methodwatch.assert_not_called()
    testdir.runpytest('-G')
    methodwatch.assert_called()


def test_print_coverage(testdir, methodwatch):
    methodwatch.watch('brownie.test.output.print_coverage_totals')
    testdir.runpytest('--coverage')
    methodwatch.assert_called()
    methodwatch.reset()
    testdir.runpytest()
    methodwatch.assert_not_called()
    testdir.runpytest('-C')
    methodwatch.assert_called()


def test_coverage_save_report(testdir):
    path = Path(testdir.tmpdir).joinpath('reports')
    testdir.runpytest()
    assert not len(list(path.glob('*')))
    testdir.runpytest('-C')
    assert len(list(path.glob('*'))) == 1
    testdir.runpytest('-C')
    assert len(list(path.glob('*'))) == 1
    next(path.glob('*')).open('w').write("this isn't json, is it?")
    testdir.runpytest('-C')
    assert len(list(path.glob('*'))) == 2
