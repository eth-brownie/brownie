#!/usr/bin/python3

import hypothesis

from brownie import network

from .stateful import state_machine  # NOQA: F401
from .strategies import strategy  # NOQA: F401


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
        hy_given = hypothesis.given(*given_args, **given_kwargs)
        hy_wrapped = hy_given(test)

        if hasattr(hy_wrapped, "hypothesis"):
            hy_wrapped.hypothesis.inner_test = isolation_wrapper
        return hy_wrapped

    return outer_wrapper
