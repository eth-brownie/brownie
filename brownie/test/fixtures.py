#!/usr/bin/python3

import sys

import pytest

import brownie
from brownie._config import ARGV

from .stateful import _BrownieStateMachine, state_machine


def _generate_fixture(container):
    def _fixture():
        yield container

    _fixture.__doc__ = f"Provides access to Brownie ContractContainer object '{container._name}'"
    return pytest.fixture(scope="session")(_fixture)


class PytestBrownieFixtures:
    def __init__(self, config, project):
        self.config = config
        for container in project:
            setattr(self, container._name, _generate_fixture(container))

    # fixtures
    @pytest.fixture(scope="module")
    def module_isolation(self):
        """
        Resets the test environment before and after a test module runs. This ensures
        a clean environment for the module, and that it's results will not affect
        subsequent tests.
        """
        brownie.rpc.reset()
        yield
        if not ARGV["interrupt"]:
            brownie.rpc.reset()

    @pytest.fixture
    def fn_isolation(self, module_isolation):
        """
        Performs the actions of module_isolation, takes a snapshot after all module
        scoped fixtures have run, and reverts to this snapshot at the start of each test.

        Used to ensure that each test in a module begins with an identical environment.
        """
        brownie.rpc.snapshot()
        yield
        if not ARGV["interrupt"]:
            brownie.rpc.revert()

    @pytest.fixture(scope="session")
    def accounts(self):
        """Yields an Accounts container for the active project, used to access local accounts."""
        yield brownie.accounts

    @pytest.fixture(scope="session")
    def a(self):
        """Short form of the accounts fixture."""
        yield brownie.accounts

    @pytest.fixture(scope="session")
    def history(self):
        """Yields a TxHistory container for the active project, used to access transaction data."""
        yield brownie.history

    @pytest.fixture(scope="session")
    def rpc(self):
        """Yields an Rpc object, used for interacting with the local test chain."""
        yield brownie.rpc

    @pytest.fixture(scope="session")
    def web3(self):
        """Yields an instantiated Web3 object, connected to the active network."""
        yield brownie.web3

    @pytest.fixture
    def no_call_coverage(self):
        """
        Prevents coverage evaluation on contract calls during this test. Useful for speeding
        up tests that contain many repetetive calls.
        """
        ARGV["always_transact"] = False
        yield
        ARGV["always_transact"] = ARGV["coverage"]

    @pytest.fixture(scope="session")
    def skip_coverage(self):
        """Skips a test when coverage evaluation is active."""
        # implemented in pytest_collection_modifyitems
        pass

    @pytest.fixture
    def state_machine(self):
        """Yields a rule-based state machine factory method."""

        # allows the state machine to disable pytest capturing
        capman = self.config.pluginmanager.get_plugin("capturemanager")
        _BrownieStateMachine._capman = capman

        # for posix systems we disable the cursor to make the progress spinner prettier
        if sys.platform != "win32":
            with capman.global_and_fixture_disabled():
                sys.stdout.write("\033[?25l")
                sys.stdout.flush()

        yield state_machine

        if sys.platform != "win32":
            with capman.global_and_fixture_disabled():
                sys.stdout.write("\033[?25h")
                sys.stdout.flush()
