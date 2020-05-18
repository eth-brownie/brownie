#!/usr/bin/python3

import warnings

import hypothesis
from hypothesis.errors import HypothesisDeprecationWarning

from brownie import network
from brownie.exceptions import BrownieTestWarning

from .stateful import state_machine  # NOQA: F401
from .strategies import contract_strategy, strategy  # NOQA: F401

# hypothesis warns against combining function-scoped fixtures with @given
# but in brownie this is a documented and useful behaviour
warnings.filterwarnings("ignore", category=HypothesisDeprecationWarning)


def given(*given_args, **given_kwargs):
    """Wrapper around hypothesis.given, a decorator for turning a test function
    that accepts arguments into a randomized test.

    This is the main entry point to Hypothesis when using Brownie.
    """

    def outer_wrapper(test):
        def isolation_wrapper(*args, **kwargs):
            network.rpc.snapshot()
            test(*args, **kwargs)
            network.rpc.revert()

        # hypothesis.given must wrap the target test to correctly
        # impersonate the call signature for pytest
        hy_given = _hypothesis_given(*given_args, **given_kwargs)
        hy_wrapped = hy_given(test)

        if hasattr(hy_wrapped, "hypothesis"):
            hy_wrapped.hypothesis.inner_test = isolation_wrapper
        return hy_wrapped

    return outer_wrapper


def _given_warning_wrapper(*args, **kwargs):
    warnings.warn(
        "Directly importing `hypothesis.given` may result in improper isolation"
        " between test runs. You should import `brownie.test.given` instead.",
        BrownieTestWarning,
    )
    return _hypothesis_given(*args, **kwargs)


def _apply_given_wrapper():
    hypothesis.given = _given_warning_wrapper


_hypothesis_given = hypothesis.given
