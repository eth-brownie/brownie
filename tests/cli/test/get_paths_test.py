#!/usr/bin/python3

from brownie.cli import test

TEST_PATHS = [
    "token/transfer.py",
    "token/approve_transferFrom.py",
    "brownie_tester/donothing.py"
]


def test_get_paths_all():
    paths = [str(i) for i in test.get_test_paths(None)]
    assert paths == [str(i) for i in test.get_test_paths('tests/')]
    assert len(paths) == 3
    for path in TEST_PATHS:
        assert len([i for i in paths if path in i]) == 1


def test_get_paths_folder():
    paths = [str(i) for i in test.get_test_paths('token')]
    assert paths == [str(i) for i in test.get_test_paths('tests/token')]
    assert len(paths) == 2
    for path in TEST_PATHS[:-1]:
        assert len([i for i in paths if path in i]) == 1


def test_get_paths_file():
    for path in TEST_PATHS:
        paths = [str(i) for i in test.get_test_paths(path)]
        assert len(paths) == 1
        assert path in paths[0]
