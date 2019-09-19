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
    assemble_contract_jobs,
    update_contract_jobs_with_dependencies,
    send_to_mythx,
    update_report,
)
from mythx_models.response import DetectedIssuesResponse


with open(str(Path(__file__).parent / "test-artifact.json"), "r") as artifact_f:
    TEST_ARTIFACT = json.load(artifact_f)

with open(str(Path(__file__).parent / "test-report.json"), "r") as artifact_f:
    TEST_REPORT = json.load(artifact_f)


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


def test_contract_job_assembly():
    contracts = {"SafeMath"}
    build = mock.MagicMock()
    build.get = lambda x: TEST_ARTIFACT

    job_data = assemble_contract_jobs(build, contracts)
    assert len(job_data) == 1
    assert job_data["SafeMath"] == construct_request_from_artifact(TEST_ARTIFACT)


def test_contract_job_updates():
    contracts = {"SafeMath"}
    libraries = {"SafeMath2"}

    build = mock.MagicMock()
    build.get = lambda x: TEST_ARTIFACT

    job_data = assemble_contract_jobs(build, contracts)

    artifact = deepcopy(TEST_ARTIFACT)
    artifact["contractName"] = "SafeMath2"
    artifact["sourcePath"] = "contracts/SafeMath2.sol"
    build.get = lambda x: artifact
    build.get_dependents = lambda x: ["SafeMath"]
    job_data = update_contract_jobs_with_dependencies(build, contracts, libraries, job_data)

    assert len(job_data["SafeMath"]["sources"]) == 2
    assert "contracts/SafeMath.sol" in job_data["SafeMath"]["sources"]
    assert "contracts/SafeMath2.sol" in job_data["SafeMath"]["sources"]

    assert (
        job_data["SafeMath"]["sources"]["contracts/SafeMath.sol"]
        == construct_source_dict_from_artifact(TEST_ARTIFACT)["contracts/SafeMath.sol"]
    )
    assert (
        job_data["SafeMath"]["sources"]["contracts/SafeMath2.sol"]
        == construct_source_dict_from_artifact(artifact)["contracts/SafeMath2.sol"]
    )


JOB_DATA = {
    "SafeMath": {
        "contract_name": "SafeMath",
        "bytecode": "60556023600b82828239805160001a607314601657fe5b30600052607381538281f3fe73000000000000000000000000000000000000000030146080604052600080fdfea265627a7a72315820893edda58cfc8ab942d57dfc258288727bcaf844e6397a37aefea97a87eee32464736f6c634300050b0032",
        "deployed_bytecode": "73000000000000000000000000000000000000000030146080604052600080fdfea265627a7a72315820893edda58cfc8ab942d57dfc258288727bcaf844e6397a37aefea97a87eee32464736f6c634300050b0032",
        "source_map": "25:497:0:-;;132:2:-1;166:7;155:9;146:7;137:37;255:7;249:14;246:1;241:23;235:4;232:33;222:2;;269:9;222:2;293:9;290:1;283:20;323:4;314:7;306:22;347:7;338;331:24",
        "deployed_source_map": "25:497:0:-;;;;;;;;",
        "sources": {
            "contracts/SafeMath.sol": {
                "source": "pragma solidity ^0.5.0;\n\nlibrary SafeMath {\n    function add(uint a, uint b) internal pure returns (uint c) {\n        c = a + b;\n        require(c >= a);\n    }\n    function sub(uint a, uint b) internal pure returns (uint c) {\n        require(b <= a);\n        c = a - b;\n    }\n    function mul(uint a, uint b) internal pure returns (uint c) {\n        c = a * b;\n        require(a == 0 || c / a == b);\n    }\n    function div(uint a, uint b) internal pure returns (uint c) {\n        require(b > 0);\n        c = a / b;\n    }\n}"
            }
        },
        "source_list": ["contracts/SafeMath.sol"],
        "main_source": "contracts/SafeMath.sol",
        "solc_version": "0.5.11+commit.22be8592.Linux.g++",
        "analysis_mode": "quick",
    }
}


def test_send_to_mythx_blocking(monkeypatch):
    client = mock.MagicMock()
    response = mock.MagicMock()
    response.uuid = "foo"
    client.analyze = lambda *args, **kwargs: response

    uuids = send_to_mythx(JOB_DATA, client, False)

    assert uuids == ["foo"]


def test_send_to_mythx_async(monkeypatch):
    client = mock.MagicMock()
    response = mock.MagicMock()
    response.uuid = "foo"
    client.analyze = lambda *args, **kwargs: response
    ARGV["async"] = True
    uuids = send_to_mythx(JOB_DATA, client, False)

    assert uuids == ["foo"]


def test_send_to_mythx_blocking_auth(monkeypatch):
    client = mock.MagicMock()
    response = mock.MagicMock()
    response.uuid = "foo"
    client.analyze = lambda *args, **kwargs: response
    uuids = send_to_mythx(JOB_DATA, client, True)

    assert uuids == ["foo"]


def test_send_to_mythx_async_auth(monkeypatch):
    client = mock.MagicMock()
    response = mock.MagicMock()
    response.uuid = "foo"
    client.analyze = lambda *args, **kwargs: response
    ARGV["async"] = True
    uuids = send_to_mythx(JOB_DATA, client, True)

    assert uuids == ["foo"]


def test_update_report():
    client = mock.MagicMock()
    client.report = lambda x: DetectedIssuesResponse.from_dict(TEST_REPORT)

    source_to_name = {"contracts/SafeMath.sol": "SafeMath"}
    highlight_report = {"highlights": {"MythX": {"SafeMath": {"contracts/SafeMath.sol": []}}}}

    update_report(client, "foo", highlight_report, source_to_name)
    assert highlight_report == {
        "highlights": {
            "MythX": {
                "SafeMath": {
                    "contracts/SafeMath.sol": [
                        [0, 23, "green", "SWC-103: A floating pragma is set."]
                    ]
                }
            }
        }
    }
