#!/usr/bin/python3

from brownie.cli import test


def _skip(module, name):
    return getattr(module, name), {'skip': True}


def _skip_coverage(module, name):
    return getattr(module, name), {'skip': "coverage"}


def test_get_data(test_paths):
    coverage, data = test.get_test_data(test_paths)
    assert len(coverage) == len(data) == 3


def test_get_data_skip(test_paths, monkeypatch):
    monkeypatch.setattr('brownie.cli.test._get_fn', _skip)
    coverage, data = test.get_test_data(test_paths)
    assert len(coverage) == 3
    assert not data
    monkeypatch.setattr('brownie.cli.test._get_fn', _skip_coverage)
    coverage, data = test.get_test_data(test_paths)
    assert len(coverage) == len(data) == 3


# TODO
# conditions for deleting coverage json
# empty test file
# duplicate function names
# setup or not setup
