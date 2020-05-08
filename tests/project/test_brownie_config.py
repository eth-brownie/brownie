#!/usr/bin/python3
import os

import pytest
import yaml

from brownie._config import _get_data_folder, _load_config
from brownie.network.rpc import _validate_cmd_settings


@pytest.fixture
def settings_proj(testproject):
    """Creates a config file in the testproject root folder and loads it manually."""

    # Save the following config as "brownie-config.yaml" in the testproject root
    test_brownie_config = """
    networks:
        default: development
        development:
            gas_limit: 6543210
            gas_price: 1000
            reverting_tx_gas_limit: 8765432
            default_contract_owner: false
            cmd_settings:
                gas_limit: 7654321
                block_time: 5
                default_balance: 15 milliether
                time: 2019-04-05T14:30:11Z
                accounts: 15
                evm_version: byzantium
                mnemonic: brownie2
    """
    with testproject._path.joinpath("brownie-config.yaml").open("w") as fp:
        yaml.dump(yaml.load(test_brownie_config), fp)

    # Load the networks.development config from the created file and yield it
    with testproject._path.joinpath("brownie-config.yaml").open() as fp:
        conf = yaml.safe_load(fp)["networks"]["development"]
        yield conf

    os.remove(testproject._path.joinpath("brownie-config.yaml"))


def test_load_project_cmd_settings(config, testproject, settings_proj):
    """Tests if project specific cmd_settings update the network config when a project is loaded"""
    # get raw cmd_setting config data from the network-config.yaml file
    config_path_network = _get_data_folder().joinpath("network-config.yaml")
    cmd_settings_network_raw = _load_config(config_path_network)["development"][0]["cmd_settings"]

    # compare the manually loaded cmd_settings to the cmd_settings in the CONFIG singleton
    cmd_settings_config = config.networks["development"]["cmd_settings"]
    for k, v in cmd_settings_config.items():
        if k != "port":
            assert cmd_settings_network_raw[k] == v

    # Load the project with its project specific settings and assert that the CONFIG was updated
    testproject.load_config()
    cmd_settings_config = config.networks["development"]["cmd_settings"]
    for k, v in settings_proj["cmd_settings"].items():
        if k != "port":
            assert cmd_settings_config[k] == v


def test_rpc_project_cmd_settings(devnetwork, testproject, config, settings_proj):
    """Test if project specific settings are properly passed on to the RPC."""
    if devnetwork.rpc.is_active():
        devnetwork.rpc.kill()
    cmd_settings_proj = settings_proj["cmd_settings"]
    testproject.load_config()
    devnetwork.connect("development")

    # Check if rpc time is roughly the start time in the config file
    # Use diff < 25h to dodge potential timezone differences
    assert cmd_settings_proj["time"].timestamp() - devnetwork.rpc.time() < 60 * 60 * 25

    accounts = devnetwork.accounts
    assert cmd_settings_proj["accounts"] == len(accounts)
    assert cmd_settings_proj["default_balance"] == accounts[0].balance()

    # Test if mnemonic was updated to "brownie2"
    assert "0x816200940a049ff1DEAB864d67a71ae6Dd1ebc3e" == accounts[0].address

    tx = accounts[0].transfer(accounts[1], 0)
    assert tx.gas_limit == settings_proj["gas_limit"]
    assert tx.gas_price == settings_proj["gas_price"]

    assert devnetwork.rpc.evm_version() == cmd_settings_proj["evm_version"]
    devnetwork.rpc.kill()


def test_validate_cmd_settings():
    cmd_settings = """
        port: 1
        gas_limit: 2
        block_time: 3
        time: 2019-04-05T14:30:11
        accounts: 4
        evm_version: istanbul
        mnemonic: brownie
        account_keys_path: ../../
        fork: main
    """
    cmd_settings_dict = yaml.load(cmd_settings)
    valid_dict = _validate_cmd_settings(cmd_settings_dict)
    for (k, v) in cmd_settings_dict.items():
        assert valid_dict[k] == v


@pytest.mark.parametrize(
    "invalid_setting",
    ({"port": "foo"}, {"gas_limit": 3.5}, {"block_time": [1]}, {"time": 1}, {"mnemonic": 0}),
)
def test_raise_validate_cmd_settings(invalid_setting):
    with pytest.raises(TypeError):
        _validate_cmd_settings(invalid_setting)
