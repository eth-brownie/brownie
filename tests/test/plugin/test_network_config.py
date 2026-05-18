#!/usr/bin/python3

import pytest


@pytest.fixture(autouse=True)
def plugin_network_port(config, network_name, xdist_id):
    port = 8765 + xdist_id
    config.networks[network_name]["cmd_settings"]["port"] = port
    return port


def test_plugin_child_network_config_sync(plugintester, network_name, plugin_network_port):
    plugintester.makepyfile(
        f"""
import yaml

from brownie._config import _get_data_folder


def test_child_network_config_sync():
    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        network_config = yaml.safe_load(fp)

    network = next(i for i in network_config["development"] if i["id"] == {network_name!r})
    assert network["cmd_settings"]["port"] == {plugin_network_port}
"""
    )
    result = plugintester.runpytest()
    result.assert_outcomes(passed=1)
