#!/usr/bin/python3

from pathlib import Path
import pytest

import brownie
from .update import UpdateManager
from . import output, coverage
from brownie._config import CONFIG, ARGV


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


if brownie.project.check_for_project('.'):

    for container in brownie.project.load():
        globals()[container._name] = generate_fixture(
            container,
            f"Provides access to the brownie ContractContainer object '{container._name}'"
        )

    u = UpdateManager(Path(CONFIG['folders']['project']).joinpath('build/tests.json'))

    def pytest_addoption(parser):
        parser.addoption(
            '--coverage', '-C', action="store_true", help="Evaluate contract test coverage"
        )
        parser.addoption(
            '--gas', '-G', action="store_true", help="Display gas profile for function calls"
        )
        parser.addoption(
            '--update', '-U', action="store_true", help="Only run tests where changes have occurred"
        )
        parser.addoption(
            '--network',
            '-N',
            default=False,
            nargs=1,
            help=f"Use a specific network (default {CONFIG['network_defaults']['name']})"
        )

    def pytest_configure(config):
        if config.getoption("--coverage"):
            ARGV['coverage'] = True
            ARGV['always_transact'] = True
        if config.getoption("--gas"):
            ARGV['gas'] = True
        if config.getoption('--network'):
            ARGV['network'] = config.getoption('--network')[0]

    def pytest_collect_file(path, parent):
        if Path(path).name == "conftest.py":
            u.add_setup(path)
            pass

    def pytest_collection_modifyitems(session, config, items):
        tests = {}
        for i in items:
            path = i.parent.fspath
            if 'module_isolation' not in i.fixturenames:
                tests[path] = None
                continue
            if path in tests and tests[path] is None:
                continue
            tests.setdefault(i.parent.fspath, []).append(i)
        tests = dict((k, v) for k, v in tests.items() if v)
        u.set_isolated(set(tests))
        if not config.getoption('--update'):
            return
        for path in filter(u.check_updated, tests):
            for i in tests[path]:
                i.add_marker("skip")

    def pytest_runtestloop():
        brownie.network.connect(ARGV['network'])
        pytest.reverts = RevertContextManager

    def pytest_runtest_teardown(item, nextitem):
        # called before teardown, use to check if this was last test in the module
        if not nextitem or item.parent.fspath != nextitem.parent.fspath:
            u.finish_module(item.parent.fspath)

    def pytest_runtest_logfinish(nodeid, location):
        # called after teardown - if runtest_teardown says this was last test, save the json
        pass

    def pytest_sessionfinish():
        if ARGV['coverage']:

            coverage_eval = brownie.history.get_coverage()
            coverage_eval = coverage.merge(coverage_eval)

            output.print_coverage_totals(coverage_eval)
            output.save_coverage_report(
                coverage_eval,
                Path(CONFIG['folders']['project']).joinpath("reports")
            )
        if ARGV['gas']:
            output.print_gas_profile()

    # fixtures
    @pytest.fixture(scope="module")
    def module_isolation(request):
        brownie.rpc.reset()
        yield
        brownie.rpc.reset()

    @pytest.fixture()
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

    @pytest.fixture()
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

    @pytest.fixture()
    def no_call_coverage():
        ARGV['always_transact'] = False
        yield
        ARGV['always_transact'] = ARGV['coverage']
