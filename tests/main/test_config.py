#!/usr/bin/python3

import json

import pytest

from brownie._config import _load_config


def test_base_keys(config):
    assert set(config) == {"network", "pytest", "compiler", "colors", "active_network"}


def test_network_keys(config):
    assert set(config["network"]) == {"default", "settings", "networks"}
    assert set(config["network"]["networks"]) == {
        "development",
        "mainnet",
        "goerli",
        "kovan",
        "rinkeby",
        "ropsten",
        "classic",
        "kotti"
    }


def test_setitem(config):
    with pytest.raises(KeyError):
        config["foo"] = "bar"
    config._unlock()
    config["foo"] = "bar"


def test_load_yaml_before_json(tmp_path):
    with pytest.raises(ValueError):
        _load_config(tmp_path)
    with tmp_path.joinpath("brownie-config.json").open("w") as fp:
        fp.write("""{"foo":"json"}""")
    assert _load_config(tmp_path) == {"foo": "json"}
    with tmp_path.joinpath("brownie-config.yaml").open("w") as fp:
        fp.write("""{"foo":"yaml"}""")
    assert _load_config(tmp_path) == {"foo": "yaml"}


def test_project_config_overwrites_default(testproject, config):
    assert config["network"]["default"] != "ropsten"
    conf_copy = config._copy()
    conf_copy["network"]["default"] = "ropsten"
    with testproject._path.joinpath("brownie-config.yaml").open("w") as fp:
        json.dump(conf_copy, fp, default=str)
    testproject.load_config()
    assert config["network"]["default"] == "ropsten"
