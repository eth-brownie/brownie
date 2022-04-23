from pathlib import Path

import pytest
import solcx

from brownie.project import load, new
from brownie.project.compiler.solidity import find_best_solc_version

sources = [
    (
        "contracts/Foo.sol",
        """
contract Foo {
    uint256 value_;
    function value() external view returns(uint256) {
        return value_;
    }
}
    """,
    ),
    (
        "contracts/Baz.sol",
        """
enum Test {
    A,
    B,
    C,
    D
}

contract Baz {}
    """,
    ),
    (
        "contracts/Bar.sol",
        """
import {Foo as FooSomething} from "./Foo.sol";
import './Baz.sol';

struct Helper {
    address x;
    uint256 y;
    uint8 z;
}

contract Bar is FooSomething {}
    """,
    ),
]


@pytest.mark.parametrize("version", ("0.6.0", "0.7.3", "0.8.6"))
def test_verification_info(tmp_path_factory, version):
    header = f"""
// SPDX-License-Identifier: MIT
pragma solidity {version};


    """

    # setup directory
    dir: Path = tmp_path_factory.mktemp("verify-project")
    # initialize brownie project
    new(dir.as_posix())

    modded_sources = {}
    for fp, src in sources:
        with dir.joinpath(fp).open("w") as f:
            f.write(header + src)
        modded_sources[fp] = header + src

    find_best_solc_version(modded_sources, install_needed=True)

    project = load(dir, "TestImportProject")

    for contract_name in ("Foo", "Bar", "Baz"):
        contract = getattr(project, contract_name)
        input_data = contract.get_verification_info()["standard_json_input"]

        # output selection isn't included in the verification info because
        # etherscan replaces it regardless. Here we just replicate with what they
        # would include
        input_data["settings"]["outputSelection"] = {
            "*": {"*": ["evm.bytecode", "evm.deployedBytecode", "abi"]}
        }

        compiler_version, _ = contract._build["compiler"]["version"].split("+")
        output_data = solcx.compile_standard(input_data, solc_version=compiler_version)
        # keccak256 = 0xd61b13a841b15bc814760b36086983db80788946ca38aa90a06bebf287a67205
        build_info = output_data["contracts"][f"{contract_name}.sol"][contract_name]

        assert build_info["abi"] == contract.abi
        # ignore the metadata at the end of the bytecode, etherscan does the same
        assert build_info["evm"]["bytecode"]["object"][:-96] == contract.bytecode[:-96]
        assert (
            build_info["evm"]["deployedBytecode"]["object"][:-96]
            == contract._build["deployedBytecode"][:-96]
        )
    project.close()
