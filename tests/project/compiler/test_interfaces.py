import json

solc_interface = """
pragma solidity ^0.6.0;
interface Foo { event myEvent(); }
interface Bar { event myOtherEvent(); }
"""

solc_import_interface = """
pragma solidity ^0.6.0;
import "../Foo.sol";
interface Baz is Foo { event BazEvent(); }
"""

vyper_contract = """
@external
def foo() -> bool:
    return True
"""

vyper_interface = """
@external
def foo() -> bool:
    pass
"""


abi = [
    {
        "constant": True,
        "inputs": [],
        "name": "version",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    }
]


def test_compile_interfaces(newproject):
    with newproject._path.joinpath("interfaces/Foo.sol").open("w") as fp:
        fp.write(solc_interface)
    newproject.load()

    assert hasattr(newproject.interface, "Foo")
    assert hasattr(newproject.interface, "Bar")


def test_interface_imports(newproject):
    with newproject._path.joinpath("interfaces/Foo.sol").open("w") as fp:
        fp.write(solc_interface)

    newproject._path.joinpath("interfaces/baz").mkdir()
    with newproject._path.joinpath("interfaces/baz/Baz.sol").open("w") as fp:
        fp.write(solc_import_interface)
    newproject.load()

    assert hasattr(newproject.interface, "Baz")


def test_json_interface(newproject):
    with newproject._path.joinpath("interfaces/Foo.json").open("w") as fp:
        json.dump(abi, fp)
    newproject.load()

    assert hasattr(newproject.interface, "Foo")


def test_vyper_interface(newproject):
    with newproject._path.joinpath("interfaces/Foo.vy").open("w") as fp:
        fp.write(vyper_contract)

    with newproject._path.joinpath("interfaces/Bar.vy").open("w") as fp:
        fp.write(vyper_interface)
    newproject.load()

    assert hasattr(newproject.interface, "Foo")
    assert not hasattr(newproject.interface, "Bar")
