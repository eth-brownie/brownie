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


def _write_project_sources(dir: Path, sources: list[tuple[str, str]], header: str = "") -> dict:
    modded_sources = {}
    for fp, src in sources:
        dir.joinpath(fp).parent.mkdir(parents=True, exist_ok=True)
        with dir.joinpath(fp).open("w") as f:
            f.write(header + src)
        modded_sources[fp] = header + src
    return modded_sources


def _compile_verification_info(contract):
    input_data = contract.get_verification_info()["standard_json_input"]
    input_data["settings"]["outputSelection"] = {
        "*": {"*": ["evm.bytecode", "evm.deployedBytecode", "abi"]}
    }
    compiler_version, _ = contract._build["compiler"]["version"].split("+")
    return input_data, solcx.compile_standard(input_data, solc_version=compiler_version)


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

    modded_sources = _write_project_sources(dir, sources, header)

    find_best_solc_version(modded_sources, install_needed=True)

    project = load(dir, "TestImportProject")

    for contract_name in ("Foo", "Bar", "Baz"):
        contract = getattr(project, contract_name)
        input_data, output_data = _compile_verification_info(contract)
        source_path = contract._build["sourcePath"]
        assert source_path in input_data["sources"]
        build_info = output_data["contracts"][source_path][contract_name]

        assert build_info["abi"] == contract.abi
        # ignore the metadata at the end of the bytecode, etherscan does the same
        assert build_info["evm"]["bytecode"]["object"][:-96] == contract.bytecode[:-96]
        assert (
            build_info["evm"]["deployedBytecode"]["object"][:-96]
            == contract._build["deployedBytecode"][:-96]
        )
    project.close()


def test_verification_info_preserves_duplicate_basenames(tmp_path_factory):
    dir: Path = tmp_path_factory.mktemp("verify-duplicate-basenames")
    new(dir.as_posix())
    duplicate_sources = [
        (
            "contracts/a/Shared.sol",
            """
// SPDX-License-Identifier: MIT
pragma solidity 0.6.0;
contract SharedA {}
            """,
        ),
        (
            "contracts/b/Shared.sol",
            """
// SPDX-License-Identifier: MIT
pragma solidity 0.6.0;
contract SharedB {}
            """,
        ),
        (
            "contracts/UsesShared.sol",
            """
// SPDX-License-Identifier: MIT
pragma solidity 0.6.0;
import {SharedA} from "./a/Shared.sol";
import {SharedB} from "./b/Shared.sol";
contract UsesShared is SharedA, SharedB {}
            """,
        ),
    ]
    modded_sources = _write_project_sources(dir, duplicate_sources)
    find_best_solc_version(modded_sources, install_needed=True)

    project = load(dir, "DuplicateBasenameProject")
    input_data, output_data = _compile_verification_info(project.UsesShared)

    assert {"contracts/a/Shared.sol", "contracts/b/Shared.sol"}.issubset(
        input_data["sources"]
    )
    assert "UsesShared" in output_data["contracts"]["contracts/UsesShared.sol"]
    project.close()


def test_verification_info_keys_libraries_by_source_path(accounts, tmp_path_factory):
    dir: Path = tmp_path_factory.mktemp("verify-linked-library")
    new(dir.as_posix())
    linked_sources = [
        (
            "contracts/lib/TestLib.sol",
            """
// SPDX-License-Identifier: MIT
pragma solidity 0.6.0;
library TestLib {
    function add(uint256 a, uint256 b) external pure returns (uint256) {
        return a + b;
    }
}
            """,
        ),
        (
            "contracts/UsesLib.sol",
            """
// SPDX-License-Identifier: MIT
pragma solidity 0.6.0;
import {TestLib} from "./lib/TestLib.sol";
contract UsesLib {
    function add(uint256 a, uint256 b) external view returns (uint256) {
        return TestLib.add(a, b);
    }
}
            """,
        ),
    ]
    modded_sources = _write_project_sources(dir, linked_sources)
    find_best_solc_version(modded_sources, install_needed=True)

    project = load(dir, "LinkedLibraryVerificationProject")
    lib = accounts[0].deploy(project.TestLib)
    input_data, output_data = _compile_verification_info(project.UsesLib)

    libraries = input_data["settings"]["libraries"]
    assert libraries == {"contracts/lib/TestLib.sol": {"TestLib": lib.address}}
    assert "UsesLib" in output_data["contracts"]["contracts/UsesLib.sol"]
    project.close()
