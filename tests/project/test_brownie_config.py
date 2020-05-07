#!/usr/bin/python3

import pytest
import yaml

from brownie._config import _get_data_folder, _load_config


@pytest.fixture
def settings_proj(testprojectconfig):
    with testprojectconfig._path.joinpath("brownie-config.yaml").open() as fp:
        settings_proj_raw = yaml.safe_load(fp)["networks"]["development"]
    yield settings_proj_raw


def test_load_project_cmd_settings(config, testprojectconfig, settings_proj):
    """Tests if project specific cmd_settings update the network config when a project is loaded"""
    # get raw cmd_setting config data from files
    config_path_network = _get_data_folder().joinpath("network-config.yaml")
    cmd_settings_network_raw = _load_config(config_path_network)["development"][0]["cmd_settings"]

    # compare initial settings to network config
    cmd_settings_network = config.networks["development"]["cmd_settings"]
    for k, v in cmd_settings_network.items():
        if k != "port":
            assert cmd_settings_network_raw[k] == v

    # load project and check if settings correctly updated
    testprojectconfig.load_config()
    cmd_settings_proj = config.networks["development"]["cmd_settings"]
    for k, v in settings_proj["cmd_settings"].items():
        if k != "port":
            assert cmd_settings_proj[k] == v


def test_rpc_project_cmd_settings(devnetwork, testprojectconfig, config, settings_proj):
    """Test if project specific settings are properly passed on to the RPC."""
    if devnetwork.rpc.is_active():
        devnetwork.rpc.kill()
    cmd_settings_proj = settings_proj["cmd_settings"]
    testprojectconfig.load_config()
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
