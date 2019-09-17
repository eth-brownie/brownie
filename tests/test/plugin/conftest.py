#!/usr/bin/python3

from pathlib import Path

import pytest


@pytest.fixture
def json_path(plugintester):
    yield Path(plugintester.tmpdir).joinpath("build/tests.json")
