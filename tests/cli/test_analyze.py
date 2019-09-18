import json
from copy import deepcopy
from pathlib import Path

import pytest

from brownie._cli.analyze import construct_source_dict_from_artifact, construct_request_from_artifact


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

    assert construct_request_from_artifact(
        artifact
    )["bytecode"] == "0x00000000000000000000000000000000000000000000000000"


def test_request_deployed_bytecode_patch():
    artifact = deepcopy(TEST_ARTIFACT)
    artifact["deployedBytecode"] = "0x00000000__$aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa$__00000000000000000000"

    assert construct_request_from_artifact(
        artifact
    )["deployed_bytecode"] == "0x00000000000000000000000000000000000000000000000000000000000000000000"


@pytest.mark.parametrize("artifact_file,key,value", (
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
        (TEST_ARTIFACT, "analysis_mode", "quick")
))
def test_request_from_artifact(artifact_file, key, value):
    request_dict = construct_request_from_artifact(artifact_file)
    assert request_dict[key] == value
