#!/usr/bin/python3

import pytest


@pytest.fixture(autouse=True)
def ipfs_setup(ipfs_mock):
    pass


@pytest.fixture
def tp_path(testproject):
    yield testproject._path
