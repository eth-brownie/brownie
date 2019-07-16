#!/usr/bin/python3

import json
import pytest

conf_source = '''
import pytest

@pytest.fixture(autouse=True)
def isolation(module_isolation):
    pass'''

test_source = '''
def test_stuff(Token, accounts):
    token = accounts[0].deploy(Token, "Test Token", "TST", 18, "1000 ether")
    token.transfer(accounts[1], "10 ether", {'from': accounts[0]})'''


@pytest.fixture
def runconf(testdir):
    testdir.makeconftest(conf_source)
    result = testdir.runpytest('-U')
    result.assert_outcomes(passed=1)


def test_update_no_isolation(testdir):
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
    result = testdir.runpytest('-U')
    result.assert_outcomes(passed=1)


def test_update_isolation(runconf, testdir):
    result = testdir.runpytest('-U')
    result.assert_outcomes(skipped=1)


def test_update_isolation_coverage(runconf, testdir):
    result = testdir.runpytest('-C', '-U')
    result.assert_outcomes(passed=1)
    result = testdir.runpytest('-C', '-U')
    result.assert_outcomes(skipped=1)
    result = testdir.runpytest('-U')
    result.assert_outcomes(skipped=1)
    testdir.runpytest()
    result = testdir.runpytest('-C', '-U')
    result.assert_outcomes(skipped=1)


def test_update_isolation_contract_changed(runconf, json_path, testdir):
    with json_path.open() as fp:
        build = json.load(fp)
    build['contracts']['Token'] = "potato"
    with json_path.open('w') as fp:
        build = json.dump(build, fp)

    result = testdir.runpytest('-U')
    result.assert_outcomes(passed=1)


def test_update_isolation_testfile_changed(runconf, json_path, testdir):
    with json_path.open() as fp:
        build = json.load(fp)
    build['tests']['test_update_isolation_testfile_changed.py']['sha1'] = "potato"
    with json_path.open('w') as fp:
        build = json.dump(build, fp)

    result = testdir.runpytest('-U')
    result.assert_outcomes(passed=1)
