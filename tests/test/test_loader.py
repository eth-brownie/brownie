#!/usr/bin/python3

from brownie.test import loader


def test_import_from_path():
    module = loader.import_from_path('tests/brownie-test-project/scripts/token.py')
    assert module.__name__ == "scripts.token"
    assert hasattr(module, "main")


def test_get_methods():
    path = 'tests/brownie-test-project/tests/token/approve_transferFrom.py'
    data = loader.get_methods(path)
    fn_names = [i[0].__name__ for i in data]
    assert fn_names[0] == "setup"
    assert "balance" in fn_names, "skipped method was not included"
    assert not data[-1][1]['pending']
    assert 'test_param' in data[-1][1]
    data = loader.get_methods(path, check_coverage=True)
    assert data[-1][1]['pending'], "pending was not true with coverage flag"
