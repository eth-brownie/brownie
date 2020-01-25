#!/usr/bin/python3

import pytest


@pytest.fixture
def SMTestBase(devnetwork):
    class _Base:
        def rule_one(self):
            pass

        def rule_two(self):
            pass

    yield _Base
