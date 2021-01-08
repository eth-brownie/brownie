import pytest

INTERFACE = """
pragma solidity ^0.5.0;

{} Foo {{
    function baz() external returns (bool);
}}
"""

CONTRACT = """
pragma solidity ^0.5.0;

import "{}interfaces/Foo.sol";

contract Bar is Foo {{
    function baz() external returns (bool) {{
        return true;
    }}
}}
"""


def test_in_contracts_folder(newproject):
    with newproject._path.joinpath("contracts/Foo.sol").open("w") as fp:
        fp.write(INTERFACE.format("interface"))
    newproject.load()
    assert newproject._path.joinpath("build/contracts/Foo.json").exists()
    assert not hasattr(newproject, "Foo")
    assert hasattr(newproject.interface, "Foo")


@pytest.mark.parametrize("contract_type", ("contract", "interface"))
def test_in_interfaces_folder(newproject, contract_type):
    with newproject._path.joinpath("interfaces/Foo.sol").open("w") as fp:
        fp.write(INTERFACE.format(contract_type))
    newproject.load()
    assert not newproject._path.joinpath("build/contracts/Foo.json").exists()
    assert not hasattr(newproject, "Foo")
    assert hasattr(newproject.interface, "Foo")


@pytest.mark.parametrize("import_path", ("../", ""))
@pytest.mark.parametrize("contract_type", ("contract", "interface"))
def test_contract_requires_interface(newproject, contract_type, import_path):
    with newproject._path.joinpath("interfaces/Foo.sol").open("w") as fp:
        fp.write(INTERFACE.format(contract_type))
    with newproject._path.joinpath("contracts/Bar.sol").open("w") as fp:
        fp.write(CONTRACT.format(import_path))
    newproject.load()
    assert newproject._path.joinpath("build/interfaces/Foo.json").exists()
    assert not newproject._path.joinpath("build/contracts/Foo.json").exists()
    assert not hasattr(newproject, "Foo")


def test_incompatible_interface_version(newproject):
    with newproject._path.joinpath("interfaces/Foo.sol").open("w") as fp:
        fp.write(INTERFACE.format("interface"))
    with newproject._path.joinpath("contracts/Bar.sol").open("w") as fp:
        fp.write(CONTRACT.format(""))
    with newproject._path.joinpath("interfaces/Baz.sol").open("w") as fp:
        fp.write("pragma solidity ^0.4.0; interface X { function baz() external returns (bool); }")
    newproject.load()
