#!/usr/bin/python3

import pytest

import brownie
from brownie._config import ARGV


def _generate_fixture(container):
    def _fixture():
        yield container

    _fixture.__doc__ = f"Provides access to Brownie ContractContainer object '{container._name}'"
    return pytest.fixture(scope="session")(_fixture)


class TestFixtures:
    def __init__(self, config, project):
        self.config = config
        for container in project:
            setattr(self, container._name, _generate_fixture(container))

    # fixtures
    @pytest.fixture(scope="module")
    def module_isolation(self):
        brownie.rpc.reset()
        yield
        if not ARGV["interrupt"]:
            brownie.rpc.reset()

    @pytest.fixture
    def fn_isolation(self, module_isolation):
        brownie.rpc.snapshot()
        yield
        if not ARGV["interrupt"]:
            brownie.rpc.revert()

    @pytest.fixture(scope="session")
    def a(self):
        yield brownie.accounts

    @pytest.fixture(scope="session")
    def accounts(self):
        yield brownie.accounts

    @pytest.fixture(scope="session")
    def history(self):
        yield brownie.history

    @pytest.fixture(scope="session")
    def rpc(self):
        yield brownie.rpc

    @pytest.fixture(scope="session")
    def web3(self):
        yield brownie.web3

    @pytest.fixture
    def no_call_coverage(self):
        ARGV["always_transact"] = False
        yield
        ARGV["always_transact"] = ARGV["coverage"]

    @pytest.fixture
    def skip_coverage(self):
        # implemented in pytest_collection_modifyitems
        pass
