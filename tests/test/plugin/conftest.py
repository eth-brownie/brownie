#!/usr/bin/python3

from pathlib import Path

import pytest


@pytest.fixture
def json_path(plugintester):
    yield Path(plugintester.tmpdir).joinpath("build/tests.json")


@pytest.fixture
def isolatedtester(plugintester):
    conf_source = """
import pytest

@pytest.fixture(autouse=True)
def isolation(module_isolation):
    pass
    """
    plugintester.makeconftest(conf_source)
    yield plugintester
