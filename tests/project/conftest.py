#!/usr/bin/python3

import pytest

from brownie.project import sources


@pytest.fixture(scope="module")
def solc5source():
    source = sources.get('BrownieTester')
    source = source.replace('BrownieTester', 'TempTester')
    source = source.replace('UnlinkedLib', 'TestLib')
    yield source


@pytest.fixture(scope="module")
def solc4source(solc5source):
    source = solc5source
    source = source.replace('payable ', '')
    source = source.replace('^0.5.0', '^0.4.25')
    yield source
