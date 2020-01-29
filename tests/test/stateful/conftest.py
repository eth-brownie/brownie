#!/usr/bin/python3

import pytest
from hypothesis import settings

# derandomizing prevents flaky test outcomes
# we are testing hypothesis itself, not testing with hypothesis
settings.register_profile("derandomize", derandomize=True)


@pytest.fixture
def SMTestBase(devnetwork):
    settings.load_profile("derandomize")

    class _Base:
        def rule_one(self):
            pass

        def rule_two(self):
            pass

    yield _Base

    settings.load_profile("default")
