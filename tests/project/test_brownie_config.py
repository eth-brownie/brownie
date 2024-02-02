#!/usr/bin/python3

import copy

import pytest
import yaml

from brownie._config import _get_data_folder, _load_config
from brownie.network import web3
from brownie.network.rpc.ganache import _validate_cmd_settings

BASE_PROJECT_CONFIG = yaml.safe_load(
    """
networks:
    default: development
    development:
        gas_limit: 6543210
        gas_price: 1000
        reverting_tx_gas_limit: 8765432
        default_contract_owner: false
        cmd_settings:
            network_id: 777
            chain_id: 666
            gas_limit: 7654321
            block_time: 5
            default_balance: 15 milliether
            time: 2019-04-05T14:30:11Z
            accounts: 15
            evm_version: byzantium
            mnemonic: brownie2
            unlock:
                - 0x16Fb96a5fa0427Af0C8F7cF1eB4870231c8154B6
                - "0x81431b69B1e0E334d4161A13C2955e0f3599381e"
"""
)


@pytest.fixture
def project_settings(testproject):
    """Creates a config file in the testproject root folder and loads it manually."""
    # Save the project config as "brownie-config.yaml" in the testproject root
    with testproject._path.joinpath("brownie-config.yaml").open("w") as fp:
        yaml.dump(BASE_PROJECT_CONFIG, fp)

    # Load the networks.development config from the created file and yield it
    with testproject._path.joinpath("brownie-config.yaml").open() as fp:
        conf = yaml.safe_load(fp)["networks"]["development"]

    yield conf


def test_load_project_cmd_settings(config, testproject, project_settings):
    """Tests if project specific cmd_settings update the network config when a project is loaded"""
    # get raw cmd_setting config data from the network-config.yaml file
    config_path_network = _get_data_folder().joinpath("network-config.yaml")
    cmd_settings_network_raw = _load_config(config_path_network)["development"][0]["cmd_settings"]

    # compare the manually loaded network cmd_settings to the cmd_settings in the CONFIG singleton
    cmd_settings_config = config.networks["development"]["cmd_settings"]
    for k, v in cmd_settings_config.items():
        if k != "port":
            assert cmd_settings_network_raw[k] == v

    # Load the project with its project specific settings and assert that the CONFIG was updated
    testproject.load_config()
    cmd_settings_config = config.networks["development"]["cmd_settings"]
    for k, v in project_settings["cmd_settings"].items():
        if k != "port":
            assert cmd_settings_config[k] == v


def test_rpc_project_cmd_settings(devnetwork, testproject, config, project_settings, network_name):
    """Test if project specific settings are properly passed on to the RPC."""
    if devnetwork.rpc.is_active():
        devnetwork.rpc.kill()
    cmd_project_settings = project_settings["cmd_settings"]
    testproject.load_config()
    devnetwork.connect(network_name)

    # Check if rpc time is roughly the start time in the config file
    # Use diff < 25h to dodge potential timezone differences
    assert cmd_project_settings["time"].timestamp() - devnetwork.chain.time() < 60 * 60 * 25

    accounts = devnetwork.accounts
    assert cmd_project_settings["accounts"] + len(cmd_project_settings["unlock"]) == len(accounts)
    assert cmd_project_settings["default_balance"] == accounts[0].balance()

    # Test if mnemonic was updated to "brownie2"
    assert "0x816200940a049ff1DEAB864d67a71ae6Dd1ebc3e" == accounts[0].address

    # Test if unlocked accounts are added to the accounts object
    assert "0x16Fb96a5fa0427Af0C8F7cF1eB4870231c8154B6" == accounts[-2].address
    assert "0x81431b69B1e0E334d4161A13C2955e0f3599381e" == accounts[-1].address

    # Test if gas limit and price are loaded from the config
    tx = accounts[0].transfer(accounts[1], 0)
    assert tx.gas_limit == project_settings["gas_limit"]
    assert tx.gas_price == project_settings["gas_price"]

    # Test if chain ID and network ID can be properly queried
    assert web3.isConnected()
    assert web3.eth.chain_id == 666
    assert web3.net.version == "777"

    devnetwork.rpc.kill()


def test_validate_cmd_settings():
    cmd_settings = """
        port: 1
        gas_limit: 2
        block_time: 3
        chain_id: 555
        network_id: 444
        time: 2019-04-05T14:30:11
        accounts: 4
        evm_version: istanbul
        mnemonic: brownie
        account_keys_path: ../../
        fork: main
        disable_cache: true
    """
    cmd_settings_dict = yaml.safe_load(cmd_settings)
    valid_dict = _validate_cmd_settings(cmd_settings_dict)
    for k, v in cmd_settings_dict.items():
        assert valid_dict[k] == v


@pytest.mark.parametrize(
    "invalid_setting",
    ({"port": "foo"}, {"gas_limit": 3.5}, {"block_time": [1]}, {"time": 1}, {"mnemonic": 0}),
)
def test_raise_validate_cmd_settings(invalid_setting):
    with pytest.raises(TypeError):
        _validate_cmd_settings(invalid_setting)


DOTENV_CONTNENTS = """
DEFAULT_BALANCE="42 miliether"
SHOW_COLORS=false
""".strip()


@pytest.fixture
def env_file(testproject):
    env_file_path = testproject._path.joinpath(".env")
    with env_file_path.open("w") as fp:
        fp.write(DOTENV_CONTNENTS)
    yield env_file_path


@pytest.fixture
def project_settings_with_dotenv(testproject, env_file):
    """Creates a config file in the testproject root folder and loads it manually."""

    project_config = copy.deepcopy(BASE_PROJECT_CONFIG)
    project_config["dotenv"] = str(env_file)
    project_config["networks"]["development"]["default_balance"] = "${DEFAULT_BALANCE}"
    if "console" not in project_config:
        project_config["console"] = {}
    project_config["console"]["show_colors"] = "${SHOW_COLORS}"

    # Save the project config as "brownie-config.yaml" in the testproject root
    with testproject._path.joinpath("brownie-config.yaml").open("w") as fp:
        yaml.dump(project_config, fp)

    # Load the networks.development config from the created file and yield it
    with testproject._path.joinpath("brownie-config.yaml").open("r") as fp:
        conf = yaml.safe_load(fp)

    yield conf


def test_dotenv_imports(config, testproject, env_file, project_settings_with_dotenv):
    config_path = _get_data_folder().joinpath("brownie-config.yaml")
    _load_config(config_path)
    testproject.load_config()
    assert config.settings["console"]["show_colors"] == False  # noqa: E712
    assert config.settings["networks"]["development"]["default_balance"] == "42 miliether"
