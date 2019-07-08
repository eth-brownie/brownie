#!/usr/bin/python3

from pathlib import Path
import pytest

import brownie
from brownie.test import output
from brownie.test.manager import TestManager
from brownie._config import CONFIG, ARGV


class RevertContextManager:

    def __init__(self, revert_msg=None):
        self.revert_msg = revert_msg

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            raise AssertionError("Transaction did not revert") from None
        if exc_type is not brownie.exceptions.VirtualMachineError:
            raise exc_type(exc_value).with_traceback(traceback)
        if self.revert_msg is None or self.revert_msg == exc_value.revert_msg:
            return True
        raise AssertionError(
            f"Unexpected revert string '{exc_value.revert_msg}'\n{exc_value.source}"
        ) from None


def _generate_fixture(container):
    def _fixture():
        yield container
    _fixture.__doc__ = f"Provides access to Brownie ContractContainer object '{container._name}'"
    return pytest.fixture(scope="session")(_fixture)


if brownie.project.check_for_project('.'):

    # load project and generate dynamic fixtures
    for container in brownie.project.load():
        globals()[container._name] = _generate_fixture(container)

    # create test manager - for reading and writing to build/test.json
    manager = TestManager(Path(CONFIG['folders']['project']))

    # set commandline options
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
            '--revert', '-R', action="store_true", help="Show detailed traceback on tx reverts"
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
        if config.getoption('--revert') or CONFIG['test']['revert_traceback']:
            ARGV['revert'] = True
        if config.getoption('--network'):
            ARGV['network'] = config.getoption('--network')[0]

    # plugin hooks

    def pytest_generate_tests(metafunc):
        # module_isolation always runs first
        fixtures = metafunc.fixturenames
        if 'module_isolation' in fixtures:
            fixtures.remove('module_isolation')
            fixtures.insert(0, 'module_isolation')
        # test_isolation always runs before other function scoped fixtures
        if 'test_isolation' not in fixtures:
            fixtures.remove('test_isolation')
            defs = metafunc._arg2fixturedefs
            idx = next((
                fixtures.index(i) for i in fixtures if
                i in defs and defs[i][0].scope == "function"
            ), len(fixtures))
            fixtures.insert(idx, 'test_isolation')

    def pytest_collection_modifyitems(session, config, items):
        # determine which modules are properly isolated
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
        manager.set_isolated_modules(tests)
        if not config.getoption('--update'):
            return
        # if update flag is active, add skip marker to unchanged tests
        for path in filter(manager.check_updated, tests):
            tests[path][0].parent.add_marker('skip')

    def pytest_runtestloop():
        brownie.network.connect(ARGV['network'])
        pytest.reverts = RevertContextManager

    def pytest_runtest_teardown(item, nextitem):
        if list(item.parent.iter_markers('skip')):
            return
        # if this is the last test in a module, record the results
        if not nextitem or item.parent.fspath != nextitem.parent.fspath:
            manager.module_completed(item.parent.fspath)

    def pytest_sessionfinish():
        if ARGV['coverage']:
            coverage_eval = brownie.test.coverage.get_merged()
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

    @pytest.fixture
    def test_isolation(module_isolation):
        brownie.rpc.snapshot()
        yield
        brownie.rpc.revert()

    @pytest.fixture(scope="session")
    def a():
        yield brownie.accounts

    @pytest.fixture(scope="session")
    def accounts():
        yield brownie.accounts

    @pytest.fixture(scope="session")
    def history():
        yield brownie.history

    @pytest.fixture(scope="session")
    def rpc():
        yield brownie.rpc

    @pytest.fixture(scope="session")
    def web3():
        yield brownie.web3

    @pytest.fixture
    def no_call_coverage():
        ARGV['always_transact'] = False
        yield
        ARGV['always_transact'] = ARGV['coverage']
