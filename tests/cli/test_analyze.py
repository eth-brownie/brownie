import json
from copy import deepcopy
from pathlib import Path
from unittest import mock
from brownie._config import ARGV

import pytest

from brownie._cli.analyze import (
    construct_source_dict_from_artifact,
    construct_request_from_artifact,
    get_mythx_client,
    get_contract_locations,
    get_contract_types,
)


with open(str(Path(__file__).parent / "test-artifact.json"), "r") as artifact_f:
    TEST_ARTIFACT = json.load(artifact_f)


def empty_field(field):
    artifact = deepcopy(TEST_ARTIFACT)
    artifact[field] = ""
    return artifact


def test_source_dict_from_artifact():
    assert construct_source_dict_from_artifact(TEST_ARTIFACT) == {
        TEST_ARTIFACT["sourcePath"]: {"source": TEST_ARTIFACT["source"]}
    }


def test_request_bytecode_patch():
    artifact = deepcopy(TEST_ARTIFACT)
    artifact["bytecode"] = "0x00000000__MyLibrary_____________________________00"

    assert (
        construct_request_from_artifact(artifact)["bytecode"]
        == "0x00000000000000000000000000000000000000000000000000"
    )


def test_request_deployed_bytecode_patch():
    artifact = deepcopy(TEST_ARTIFACT)
    artifact[
        "deployedBytecode"
    ] = "0x00000000__$aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa$__00000000000000000000"

    assert (
        construct_request_from_artifact(artifact)["deployed_bytecode"]
        == "0x00000000000000000000000000000000000000000000000000000000000000000000"
    )


@pytest.mark.parametrize(
    "artifact_file,key,value",
    (
        (TEST_ARTIFACT, "contract_name", "SafeMath"),
        (empty_field("contractName"), "contract_name", ""),
        (TEST_ARTIFACT, "bytecode", TEST_ARTIFACT["bytecode"]),
        (empty_field("bytecode"), "bytecode", None),
        (TEST_ARTIFACT, "deployed_bytecode", TEST_ARTIFACT["deployedBytecode"]),
        (empty_field("deployedBytecode"), "deployed_bytecode", None),
        (TEST_ARTIFACT, "source_map", TEST_ARTIFACT["sourceMap"]),
        (empty_field("sourceMap"), "source_map", None),
        (TEST_ARTIFACT, "deployed_source_map", TEST_ARTIFACT["deployedSourceMap"]),
        (empty_field("deployedSourceMap"), "deployed_source_map", None),
        (TEST_ARTIFACT, "source_list", TEST_ARTIFACT["allSourcePaths"]),
        (empty_field("allSourcePaths"), "source_list", None),
        (TEST_ARTIFACT, "main_source", TEST_ARTIFACT["sourcePath"]),
        (empty_field("sourcePath"), "main_source", ""),
        (TEST_ARTIFACT, "solc_version", "0.5.11+commit.22be8592.Linux.g++"),
        (TEST_ARTIFACT, "analysis_mode", "quick"),
    ),
)
def test_request_from_artifact(artifact_file, key, value):
    request_dict = construct_request_from_artifact(artifact_file)
    assert request_dict[key] == value


def assert_client_access_token():
    client, authenticated = get_mythx_client()
    assert client is not None
    assert client.access_token == "foo"
    assert client.eth_address is None
    assert client.password is None
    assert authenticated


def test_mythx_client_from_access_token_env(monkeypatch):
    monkeypatch.setenv("MYTHX_ACCESS_TOKEN", "foo")
    assert_client_access_token()
    monkeypatch.delenv("MYTHX_ACCESS_TOKEN")


def test_mythx_client_from_access_token_arg():
    ARGV["access-token"] = "foo"
    assert_client_access_token()
    del ARGV["access-token"]


def assert_client_username_password():
    client, authenticated = get_mythx_client()
    assert client is not None
    assert client.eth_address == "foo"
    assert client.password == "bar"
    assert client.access_token is None
    assert authenticated


def test_mythx_client_from_username_password_env(monkeypatch):
    monkeypatch.setenv("MYTHX_ETH_ADDRESS", "foo")
    monkeypatch.setenv("MYTHX_PASSWORD", "bar")
    assert_client_username_password()
    monkeypatch.delenv("MYTHX_ETH_ADDRESS")
    monkeypatch.delenv("MYTHX_PASSWORD")


def test_mythx_client_from_username_password_arg():
    ARGV["eth-address"] = "foo"
    ARGV["password"] = "bar"
    assert_client_username_password()
    del ARGV["eth-address"]
    del ARGV["password"]


def assert_trial_client():
    client, authenticated = get_mythx_client()
    assert client is not None
    assert client.eth_address == "0x0000000000000000000000000000000000000000"
    assert client.password == "trial"
    assert client.access_token is None
    assert client.refresh_token is None


def test_mythx_client_default():
    assert_trial_client()


def test_mythx_client_default_no_password_arg():
    ARGV["eth-address"] = "foo"
    assert_trial_client()
    del ARGV["eth-address"]


def test_mythx_client_default_no_username_arg():
    ARGV["password"] = "bar"
    assert_trial_client()
    del ARGV["password"]


def test_mythx_client_default_no_password_env(monkeypatch):
    monkeypatch.setenv("MYTHX_ETH_ADDRESS", "foo")
    assert_trial_client()
    monkeypatch.delenv("MYTHX_ETH_ADDRESS")


def test_mythx_client_default_no_username_env(monkeypatch):
    monkeypatch.setenv("MYTHX_PASSWORD", "bar")
    assert_trial_client()
    monkeypatch.delenv("MYTHX_PASSWORD")


# simulate build.items() method
BUILD_CONTAINER = {
    "foo": {"sourcePath": "foo path", "contractName": "foo contract", "type": "contract"},
    "bar": {"sourcePath": "bar path", "contractName": "bar contract", "type": "contract"},
    "baz": {"sourcePath": "baz path", "contractName": "baz contract", "type": "library"},
}


def test_contract_locations_from_build():
    assert get_contract_locations(BUILD_CONTAINER) == {
        "foo path": "foo contract",
        "bar path": "bar contract",
        "baz path": "baz contract",
    }


def test_contract_types_from_build():
    assert get_contract_types(BUILD_CONTAINER) == ({"foo", "bar"}, {"baz"})
