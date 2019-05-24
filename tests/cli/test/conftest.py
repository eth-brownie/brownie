#!/usr/bin/python3

import pytest
import sys

from brownie.cli import test


@pytest.fixture(autouse=True, scope="module")
def setup():
    argv = sys.argv
    sys.argv = ['brownie', 'test']
    yield
    sys.argv = argv


@pytest.fixture(scope="module")
def test_paths():
    yield test.get_test_paths(None)
