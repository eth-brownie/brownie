import json
from copy import deepcopy
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from mythx_models.response import DetectedIssuesResponse
from pythx import ValidationError

from brownie._cli.analyze import SubmissionPipeline, print_console_report

with open(str(Path(__file__).parent / "test-artifact.json"), "r") as artifact_f:
    TEST_ARTIFACT = json.load(artifact_f)

with open(str(Path(__file__).parent / "test-report.json"), "r") as artifact_f:
    TEST_REPORT = json.load(artifact_f)


def empty_field(field):
    artifact = deepcopy(TEST_ARTIFACT)
    artifact[field] = ""
    return artifact


def test_source_dict_from_artifact():
    assert SubmissionPipeline.construct_request_from_artifact(TEST_ARTIFACT).sources == {
        TEST_ARTIFACT["sourcePath"]: {
            "source": TEST_ARTIFACT["source"],
            "ast": TEST_ARTIFACT["ast"],
        }
    }


def test_request_bytecode_patch():
    artifact = deepcopy(TEST_ARTIFACT)
    artifact["bytecode"] = "0x00000000__MyLibrary_____________________________00"

    assert (
        SubmissionPipeline.construct_request_from_artifact(artifact).bytecode
        == "0x00000000000000000000000000000000000000000000000000"
    )


def test_request_deployed_bytecode_patch():
    artifact = deepcopy(TEST_ARTIFACT)
    artifact[
        "deployedBytecode"
    ] = "0x00000000__$aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa$__00000000000000000000"

    assert (
        SubmissionPipeline.construct_request_from_artifact(artifact).deployed_bytecode
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
        (TEST_ARTIFACT, "source_list", sorted(TEST_ARTIFACT["allSourcePaths"].values())),
        (TEST_ARTIFACT, "main_source", TEST_ARTIFACT["sourcePath"]),
        (empty_field("sourcePath"), "main_source", ""),
        (TEST_ARTIFACT, "solc_version", "0.5.11+commit.22be8592.Linux.g++"),
        (TEST_ARTIFACT, "analysis_mode", "quick"),
    ),
)
def test_request_from_artifact(artifact_file, key, value):
    request_dict = SubmissionPipeline.construct_request_from_artifact(artifact_file)
    assert getattr(request_dict, key) == value


def assert_client_access_token():
    client = SubmissionPipeline.get_mythx_client()
    assert client is not None
    assert client.api_key == "foo"
    assert client.username is None
    assert client.password is None


def test_mythx_client_from_access_token_env(monkeypatch):
    monkeypatch.setenv("MYTHX_API_KEY", "foo")
    assert_client_access_token()
    monkeypatch.delenv("MYTHX_API_KEY")


def test_mythx_client_from_access_token_arg(argv):
    argv["api-key"] = "foo"
    assert_client_access_token()


def test_without_api_key():
    with pytest.raises(ValidationError):
        SubmissionPipeline.get_mythx_client()


def test_highlighting_report(monkeypatch):
    monkeypatch.setenv("MYTHX_API_KEY", "foo")
    submission = SubmissionPipeline(
        {"test": {"sourcePath": "contracts/SafeMath.sol", "contractName": "SafeMath"}}
    )
    submission.reports = {"contracts/SafeMath.sol": DetectedIssuesResponse.from_dict(TEST_REPORT)}
    submission.generate_highlighting_report()
    assert submission.highlight_report == {
        "highlights": {
            "MythX": {
                "SafeMath": {
                    "contracts/SafeMath.sol": [
                        [
                            0,
                            23,
                            "yellow",
                            (
                                "SWC-103: A floating pragma is set.\nIt is recommended to make "
                                "a conscious choice on what version of Solidity is used for "
                                'compilation. Currently multiple versions "^0.5.0" are allowed.'
                            ),
                        ]
                    ]
                }
            }
        }
    }
    monkeypatch.delenv("MYTHX_API_KEY")


def test_stdout_report(monkeypatch):
    monkeypatch.setenv("MYTHX_API_KEY", "foo")
    submission = SubmissionPipeline(
        {"test": {"sourcePath": "contracts/SafeMath.sol", "contractName": "SafeMath"}}
    )
    submission.reports = {"contracts/SafeMath.sol": DetectedIssuesResponse.from_dict(TEST_REPORT)}
    submission.generate_stdout_report()
    assert submission.stdout_report == {"contracts/SafeMath.sol": {"LOW": 3}}
    monkeypatch.delenv("MYTHX_API_KEY")


def test_wait_without_responses(monkeypatch):
    monkeypatch.setenv("MYTHX_API_KEY", "foo")
    submission = SubmissionPipeline(
        {"test": {"sourcePath": "contracts/SafeMath.sol", "contractName": "SafeMath"}}
    )
    with pytest.raises(ValidationError):
        submission.wait_for_jobs()
    monkeypatch.delenv("MYTHX_API_KEY")


def test_wait_with_responses(monkeypatch):
    monkeypatch.setenv("MYTHX_API_KEY", "foo")
    submission = SubmissionPipeline(
        {"test": {"sourcePath": "contracts/SafeMath.sol", "contractName": "SafeMath"}}
    )
    response_mock = MagicMock()
    response_mock.uuid = "test-uuid"
    ready_mock = MagicMock()
    ready_mock.return_value = True
    report_mock = MagicMock()
    report_mock.return_value = "test-report"
    submission.responses = {"test": response_mock}
    submission.client.analysis_ready = ready_mock
    submission.client.report = report_mock

    submission.wait_for_jobs()

    assert submission.reports == {"test": "test-report"}

    monkeypatch.delenv("MYTHX_API_KEY")


def test_send_requests(monkeypatch):
    monkeypatch.setenv("MYTHX_API_KEY", "foo")
    submission = SubmissionPipeline(
        {"test": {"sourcePath": "contracts/SafeMath.sol", "contractName": "SafeMath"}}
    )
    submission.requests = {"test": MagicMock()}
    analyze_mock = MagicMock()
    group_mock = MagicMock()
    group_mock.group.identifier = "test-gid"
    response_mock = MagicMock()
    response_mock.uuid = "test-uuid"
    analyze_mock.return_value = response_mock
    submission.client.analyze = analyze_mock
    submission.client.create_group = group_mock
    submission.client.seal_group = group_mock

    submission.send_requests()

    assert submission.responses == {"test": response_mock}
    monkeypatch.delenv("MYTHX_API_KEY")


def test_prepare_requests(monkeypatch):
    monkeypatch.setenv("MYTHX_API_KEY", "foo")
    build_mock = MagicMock()
    build_mock.items = {
        "SafeMath": {
            "sourcePath": "contracts/SafeMath.sol",
            "contractName": "SafeMath",
            "type": "library",
        },
        "Token": {"sourcePath": "contracts/Token.sol", "contractName": "Token", "type": "contract"},
    }.items
    build_mock.get_dependents.return_value = ["Token"]
    submission = SubmissionPipeline(build_mock)
    submission.prepare_requests()
    assert list(submission.requests.keys()) == ["Token"]
    token_request = submission.requests["Token"]
    assert token_request.contract_name == "Token"
    assert "contracts/Token.sol" in token_request.sources.keys()
    assert "contracts/SafeMath.sol" in token_request.sources.keys()
    monkeypatch.delenv("MYTHX_API_KEY")


def test_console_notify_high():
    with patch("brownie._cli.analyze.notify") as notify_patch:
        print_console_report({"Token": {"HIGH": 2}})
        assert notify_patch.called


def test_console_notify_low():
    with patch("brownie._cli.analyze.notify") as notify_patch:
        print_console_report({"Token": {"LOW": 2}})
        assert not notify_patch.called


def test_console_notify_none():
    with patch("brownie._cli.analyze.notify") as notify_patch:
        print_console_report({"Token": {}})
        assert notify_patch.called
