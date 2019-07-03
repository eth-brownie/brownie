#!/usr/bin/python3

import pytest

import brownie
from brownie.test import output, coverage
from brownie._config import ARGV


class RevertContextManager:

    def __init__(self, revert_msg=None):
        self.revert_msg = revert_msg

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        assert exc_type is brownie.exceptions.VirtualMachineError, "Transaction did not revert"
        if self.revert_msg is not None:
            assert self.revert_msg == exc_value.revert_msg, "Unexpected revert string"
        return True


def generate_fixture(container, docstring):
    def dynamic_fixture():
        yield container
    dynamic_fixture.__doc__ = docstring
    return pytest.fixture(scope="session")(dynamic_fixture)


try:
    for container in brownie.project.load():
        globals()[container._name] = generate_fixture(
            container,
            f"Provides access to the brownie ContractContainer object '{container._name}'"
        )
except brownie.exceptions.ProjectNotFound:
    pass
else:

    def pytest_addoption(parser):
        parser.addoption(
            "--coverage",
            default=False,
            const=True,
            nargs='?',
            help="calculate contract test coverage"
        )

    def pytest_configure(config):
        if config.getoption("--coverage"):
            ARGV['coverage'] = True

    def pytest_runtestloop():
        brownie.network.connect()
        pytest.reverts = RevertContextManager

    def pytest_sessionfinish():
        if not ARGV['coverage']:
            return
        output.coverage_totals(coverage._coverage_eval)

    @pytest.fixture(scope="module")
    def module_isolation():
        brownie.rpc.reset()
        yield
        brownie.rpc.reset()

    @pytest.fixture(scope="function")
    def test_isolation(module_isolation):
        brownie.rpc.snapshot()
        yield
        brownie.rpc.revert()

    @pytest.fixture()
    def a():
        yield brownie.accounts

    @pytest.fixture()
    def accounts():
        yield brownie.accounts

    @pytest.fixture()
    def history():
        yield brownie.history

    @pytest.fixture(scope="module")
    def project():
        yield brownie.project

    @pytest.fixture()
    def rpc():
        yield brownie.rpc

    @pytest.fixture()
    def web3():
        yield brownie.web3

    @pytest.fixture()
    def brownie_config():
        yield brownie.config
