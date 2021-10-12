from pathlib import Path

import solcx

from brownie.project import load, new

import_tester_source = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.4;

import {PackageRegistry} from "./PackageRegistry.sol";

contract ImportTester is PackageRegistry {}
"""


def test_verification_info(testproject, tmp_path_factory):

    # setup directory
    dir: Path = tmp_path_factory.mktemp("verify-project")
    # initialize brownie project
    new(dir.as_posix())

    with dir.joinpath("contracts/ImportTester.sol").open("w") as f:
        f.write(import_tester_source)
    with dir.joinpath("contracts/PackageRegistry.sol").open("w") as f:
        f.write(testproject.PackageRegistry._build["source"])

    project = load(dir, "TestImportProject")
    ImportTester = project.ImportTester
    input_data = ImportTester.get_verification_info()["standard_json_input"]

    # output selection isn't included in the verification info because
    # etherscan replaces it regardless. Here we just replicate with what they
    # would include
    input_data["settings"]["outputSelection"] = {
        "*": {"*": ["evm.bytecode", "evm.deployedBytecode", "abi"]}
    }

    compiler_version, _ = ImportTester._build["compiler"]["version"].split("+")
    output_data = solcx.compile_standard(input_data, solc_version=compiler_version)
    # keccak256 = 0xd61b13a841b15bc814760b36086983db80788946ca38aa90a06bebf287a67205
    build_info = output_data["contracts"]["ImportTester.sol"]["ImportTester"]

    assert build_info["abi"] == ImportTester.abi
    # ignore the metadata at the end of the bytecode, etherscan does the same
    assert build_info["evm"]["bytecode"]["object"][:-96] == ImportTester.bytecode[:-96]
    assert (
        build_info["evm"]["deployedBytecode"]["object"][:-96]
        == ImportTester._build["deployedBytecode"][:-96]
    )
