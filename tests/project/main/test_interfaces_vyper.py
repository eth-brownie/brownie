import json

INTERFACE = """
# @version 0.2.4
@external
def baz() -> bool: pass
"""

CONTRACT = """
# @version 0.2.4
import interfaces.Bar as Bar

implements: Bar

@external
def baz() -> bool:
    return True
"""

ABI = [
    {
        "constant": False,
        "inputs": [],
        "name": "baz",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function",
    }
]


def test_vy_interface(newproject):
    with newproject._path.joinpath("contracts/Foo.vy").open("w") as fp:
        fp.write(CONTRACT)
    with newproject._path.joinpath("interfaces/Bar.vy").open("w") as fp:
        fp.write(INTERFACE)
    newproject.load()
    assert newproject._path.joinpath("build/contracts/Foo.json").exists()
    assert hasattr(newproject, "Foo")
    assert not newproject._path.joinpath("build/contracts/Bar.json").exists()
    assert not hasattr(newproject, "Bar")
    assert not hasattr(newproject.interface, "Bar")


def test_json_interface(newproject):
    with newproject._path.joinpath("contracts/Foo.vy").open("w") as fp:
        fp.write(CONTRACT)
    with newproject._path.joinpath("interfaces/Bar.json").open("w") as fp:
        json.dump(ABI, fp)
    newproject.load()
    assert newproject._path.joinpath("build/contracts/Foo.json").exists()
    assert hasattr(newproject, "Foo")
    assert not newproject._path.joinpath("build/contracts/Bar.json").exists()
    assert not hasattr(newproject, "Bar")
    assert hasattr(newproject.interface, "Bar")


def test_incompatible_interface(newproject):
    with newproject._path.joinpath("contracts/Foo.vy").open("w") as fp:
        fp.write(CONTRACT)
    with newproject._path.joinpath("interfaces/Bar.vy").open("w") as fp:
        fp.write(INTERFACE)
    with newproject._path.joinpath("interfaces/Baz.sol").open("w") as fp:
        fp.write("pragma solidity ^0.4.0; interface X { function baz() external returns (bool); }")
    newproject.load()
