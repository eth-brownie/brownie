#!/usr/bin/python3

import itertools
import json
import os
import shutil
import sys
from copy import deepcopy
from pathlib import Path

import pytest
import solcx
from _pytest.monkeypatch import MonkeyPatch
from prompt_toolkit.input.defaults import create_pipe_input

import brownie
from brownie._cli.console import Console

pytest_plugins = "pytester"


TARGET_OPTS = {
    "evm": "evmtester",
    "pm": "package_test",
    "plugin": "plugintester",
}
_dev_network = "development"


def pytest_addoption(parser):
    parser.addoption(
        "--target",
        choices=["core", "pm", "plugin"],
        default="core",
        help="Target a specific component of the tests.",
    )
    parser.addoption(
        "--evm",
        nargs=3,
        metavar=("solc_versions", "evm_rulesets", "optimizer_runs"),
        help="Run evm tests against a matrix of solc versions, evm versions, and compiler runs.",
    )
    parser.addoption(
        "--network",
        choices=["development", "hardhat"],
        default="development",
    )


# remove tests based on config flags and fixture names
def pytest_collection_modifyitems(config, items):
    if config.getoption("--network"):
        global _dev_network
        _dev_network = config.getoption("--network")

    if config.getoption("--evm"):
        target = "evm"
    else:
        target = config.getoption("--target")

    for flag, fixture in TARGET_OPTS.items():
        if target == flag:
            continue
        for test in [i for i in items if fixture in i.fixturenames]:
            items.remove(test)
    if target != "core":
        fixtures = set(TARGET_OPTS.values())
        for test in [i for i in items if not fixtures.intersection(i.fixturenames)]:
            items.remove(test)


def pytest_configure(config):
    if config.getoption("--target") == "plugin" and config.getoption("numprocesses"):
        raise pytest.UsageError("Cannot use xdist with plugin tests, try adding the '-n 0' flag")

    if config.getoption("--evm"):
        # reformat evm options - only do this once to avoid repeat queries for latest solc version
        solc_versions, evm_verions, runs = [i.split(",") for i in config.option.evm]
        runs = [int(i) for i in runs]
        if "latest" in solc_versions:
            latest_version = solcx.get_installable_solc_versions()[0]
            solc_versions.remove("latest")
            solc_versions.append(latest_version)
        config.option.evm = (evm_verions, runs, solc_versions)


def pytest_generate_tests(metafunc):
    # parametrize the evmtester fixture
    evm_config = metafunc.config.getoption("--evm")
    if "evmtester" in metafunc.fixturenames and evm_config:
        params = list(itertools.product(*evm_config))
        metafunc.parametrize("evmtester", params, indirect=True)


@pytest.fixture(scope="session")
def network_name():
    return _dev_network


# worker ID for xdist process, as an integer
@pytest.fixture(scope="session")
def xdist_id(worker_id):
    if worker_id == "master":
        return 0
    return int(worker_id.lstrip("gw"))


# ensure a clean data folder, and set unique ganache ports for each xdist worker
@pytest.fixture(scope="session", autouse=True)
def _base_config(tmp_path_factory, xdist_id, network_name):
    brownie._config.DATA_FOLDER = tmp_path_factory.mktemp(f"data-{xdist_id}")
    brownie._config._make_data_folders(brownie._config.DATA_FOLDER)

    cur = brownie.network.state.cur
    cur.close()
    cur.connect(brownie._config.DATA_FOLDER.joinpath("pytest.db"))
    cur.execute("CREATE TABLE IF NOT EXISTS sources (hash PRIMARY KEY, source)")

    if xdist_id:
        port = 8545 + xdist_id
        brownie._config.CONFIG.networks[network_name]["cmd_settings"]["port"] = port


@pytest.fixture(scope="session")
def _project_factory(tmp_path_factory):
    path = tmp_path_factory.mktemp("base")
    path.rmdir()
    shutil.copytree("tests/data/brownie-test-project", path)

    p = brownie.project.load(path, "TestProject")
    p.close()
    return path


def _copy_all(src_folder, dest_folder):
    Path(dest_folder).mkdir(exist_ok=True)
    for path in Path(src_folder).glob("*"):
        dest_path = Path(dest_folder).joinpath(path.name)
        if path.is_dir():
            shutil.copytree(path, dest_path)
        else:
            shutil.copy(path, dest_path)


# project fixtures


# creates a temporary folder and sets it as the working directory
@pytest.fixture
def project(tmp_path):
    original_path = os.getcwd()
    os.chdir(tmp_path)
    yield brownie.project
    os.chdir(original_path)
    for p in brownie.project.get_loaded_projects():
        p.close(False)


# yields a newly initialized Project that is not loaded
@pytest.fixture
def newproject(project, tmp_path):
    path = project.new(tmp_path)
    p = project.load(path, "NewProject")
    p.close()
    yield p


@pytest.fixture
def np_path(newproject):
    yield newproject._path


# copies the tester project into a temporary folder, loads it, and yields a Project object
@pytest.fixture
def testproject(_project_factory, project, tmp_path):
    path = tmp_path.joinpath("testproject")
    _copy_all(_project_factory, path)
    os.chdir(path)
    return project.load(path, "TestProject")


# same as function above but doesn't compile
@pytest.fixture
def testproject_nocompile(_project_factory, project, tmp_path):
    path = tmp_path.joinpath("testproject")
    _copy_all(_project_factory, path)
    os.chdir(path)
    return project.load(path, "TestProject", compile=False)


@pytest.fixture
def tp_path(testproject):
    yield testproject._path


@pytest.fixture
def otherproject(_project_factory, project, tmp_path):  # testproject):
    _copy_all(_project_factory, tmp_path.joinpath("otherproject"))
    return project.load(tmp_path.joinpath("otherproject"), "OtherProject")


# yields a deployed EVMTester contract
# automatically parametrized with multiple compiler versions and settings
@pytest.fixture
def evmtester(_project_factory, project, tmp_path, accounts, request):
    evm_version, runs, solc_version = request.param
    tmp_path.joinpath("contracts").mkdir()
    shutil.copyfile(
        _project_factory.joinpath("contracts/EVMTester.sol"),
        tmp_path.joinpath("contracts/EVMTester.sol"),
    )
    conf_json = {
        "evm_version": evm_version,
        "compiler": {"solc": {"version": str(solc_version), "optimize": runs > 0, "runs": runs}},
    }
    with tmp_path.joinpath("brownie-config.yaml").open("w") as fp:
        json.dump(conf_json, fp)
    p = project.load(tmp_path, "EVMProject")
    return p.EVMTester.deploy({"from": accounts[0]})


@pytest.fixture
def plugintesterbase(project, testdir, monkeypatch, network_name):
    brownie.test.coverage.clear()
    brownie.network.connect(network_name)
    monkeypatch.setattr("brownie.network.connect", lambda k: None)
    testdir.plugins.extend(["pytest-brownie", "pytest-cov"])
    yield testdir
    brownie.network.disconnect()


# setup for pytest-brownie plugin testing
@pytest.fixture
def plugintester(_project_factory, plugintesterbase, request):
    _copy_all(_project_factory, plugintesterbase.tmpdir)
    test_source = getattr(request.module, "test_source", None)
    if test_source is not None:
        if isinstance(test_source, str):
            test_source = [test_source]
        test_source = {f"tests/test_{i}.py": test_source[i] for i in range(len(test_source))}
        plugintesterbase.makepyfile(**test_source)
    yield plugintesterbase


# launches and connects to ganache, yields the brownie.network module
@pytest.fixture
def devnetwork(network, rpc, chain, network_name):
    brownie.network.connect(network_name)
    yield brownie.network
    if rpc.is_active():
        chain.reset()


# brownie object fixtures


@pytest.fixture
def accounts(devnetwork):
    yield brownie.network.accounts
    brownie.network.accounts.default = None


@pytest.fixture(scope="session")
def history():
    return brownie.network.history


@pytest.fixture
def network():
    if brownie.network.is_connected():
        brownie.network.disconnect(False)
    yield brownie.network
    if brownie.network.is_connected():
        brownie.network.disconnect(False)


@pytest.fixture(scope="session")
def rpc():
    return brownie.network.rpc


@pytest.fixture(scope="session")
def chain():
    return brownie.network.chain


@pytest.fixture(scope="session")
def web3():
    return brownie.network.web3


# configuration fixtures
# changes to config or argv are reverted during teardown


@pytest.fixture
def config():

    conf = brownie._config.CONFIG
    argv = deepcopy(conf.argv)
    networks = deepcopy(conf.networks)
    settings = conf.settings._copy()

    yield conf

    conf.argv.clear()
    conf.argv.update(argv)

    conf.networks.clear()
    conf.networks.update(networks)

    conf.settings._unlock()
    conf.settings.clear()
    conf.settings.update(settings)
    conf.settings._lock()


@pytest.fixture
def argv():
    initial = {}
    initial.update(brownie._config.CONFIG.argv)
    yield brownie._config.CONFIG.argv
    brownie._config.CONFIG.argv.clear()
    brownie._config.CONFIG.argv.update(initial)


# cli mode fixtures


@pytest.fixture
def console_mode(argv):
    argv["cli"] = "console"


@pytest.fixture
def test_mode(argv):
    argv["cli"] = "test"


@pytest.fixture
def coverage_mode(argv, test_mode):
    brownie.test.coverage.clear()
    argv["coverage"] = True
    argv["always_transact"] = True


# contract fixtures


@pytest.fixture
def BrownieTester(testproject, devnetwork):
    return testproject.BrownieTester


@pytest.fixture
def ExternalCallTester(testproject, devnetwork):
    return testproject.ExternalCallTester


@pytest.fixture
def tester(BrownieTester, accounts):
    return BrownieTester.deploy(True, {"from": accounts[0]})


@pytest.fixture
def ext_tester(ExternalCallTester, accounts):
    return ExternalCallTester.deploy({"from": accounts[0]})


@pytest.fixture
def vypertester(testproject, devnetwork, accounts):
    return testproject.VyperTester.deploy({"from": accounts[0]})


# ipfs fixtures


@pytest.fixture
def package_test():
    pass


# console mock


@pytest.fixture(scope="session", autouse=True)
def console_setup():
    def _exception(obj, *args):
        obj.resetbuffer()
        raise sys.exc_info()[0]

    monkeypatch_session = MonkeyPatch()
    monkeypatch_session.setattr("brownie._cli.console.Console.showtraceback", _exception)
    monkeypatch_session.setattr("brownie._cli.console.Console.showsyntaxerror", _exception)
    Console.prompt_input = create_pipe_input()


@pytest.fixture
def console():
    argv = sys.argv
    sys.argv = ["brownie", "console"]
    yield Console
    sys.argv = argv
