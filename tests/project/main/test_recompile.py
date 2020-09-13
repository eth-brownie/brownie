#!/usr/bin/python3

import pytest

LIBRARY = """
pragma solidity ^0.5.0;
library FooLib {
    function foo() external returns (bool) { return true; }
}
"""

INTERFACE = """
pragma solidity ^0.5.0;
interface IFoo {
    function foo() external returns (bool);
}
"""

BASE_CONTRACT = """
pragma solidity ^0.5.0;
import "./FooLib.sol";

contract BaseFoo {
    function bar() external returns (bool) { return FooLib.foo(); }
}
"""


CONTRACT = """
pragma solidity 0.5.0;
import "./BaseFoo.sol";
import "interfaces/IFoo.sol";

contract Foo is BaseFoo, IFoo {
    function foo() external returns (bool) { return true; }
}"""


@pytest.fixture
def mockproject(newproject, mocker):
    with newproject._path.joinpath("contracts/Foo.sol").open("w") as fp:
        fp.write(CONTRACT)
    with newproject._path.joinpath("contracts/BaseFoo.sol").open("w") as fp:
        fp.write(BASE_CONTRACT)
    with newproject._path.joinpath("contracts/FooLib.sol").open("w") as fp:
        fp.write(LIBRARY)
    with newproject._path.joinpath("interfaces/IFoo.sol").open("w") as fp:
        fp.write(INTERFACE)
    newproject.load()
    newproject.close()
    mocker.spy(newproject, "_compile")
    yield newproject


# a new contract should be compiled
def test_new_contract(mockproject):
    with mockproject._path.joinpath("contracts/Bar.sol").open("w") as fp:
        fp.write("""pragma solidity 0.5.0; contract Bar {}""")

    mockproject.load()
    assert sorted(mockproject._compile.call_args[0][0]) == ["contracts/Bar.sol"]


# when no files have been modified, the compiler should not run
def test_unmodified(mockproject):
    mockproject.load()
    assert not mockproject._compile.call_args[0][0]


# adding and removing an interface should not trigger a recompile
def test_new_interface(mockproject):
    path = mockproject._path.joinpath("interfaces/IBar.sol")
    with path.open("w") as fp:
        fp.write("""pragma solidity 0.5.0; interface IBar {}""")

    mockproject.load()
    assert not mockproject._compile.call_args[0][0]

    mockproject._compile.reset_mock()
    path.unlink()
    mockproject.close()
    mockproject.load()
    assert not mockproject._compile.call_args[0][0]


# modifying a contract should trigger a recompile
# base contracts, interfaces, and libraries that are inherited should not recompile
def test_modified_contract(mockproject):
    code = CONTRACT.split("\n")
    code[6] += " // a comment"
    code = "\n".join(code)
    with mockproject._path.joinpath("contracts/Foo.sol").open("w") as fp:
        fp.write(code)

    mockproject.load()
    assert sorted(mockproject._compile.call_args[0][0]) == ["contracts/Foo.sol"]


# modifying a library should recompile a dependent contract
def test_modify_library(mockproject):
    with mockproject._path.joinpath("contracts/FooLib.sol").open("w") as fp:
        fp.write(LIBRARY.replace("true", "false"))

    mockproject.load()
    assert sorted(mockproject._compile.call_args[0][0]) == [
        "contracts/BaseFoo.sol",
        "contracts/Foo.sol",
        "contracts/FooLib.sol",
    ]


# modifying a base contract should recompile a dependent
def test_modify_base(mockproject):
    code = BASE_CONTRACT.split("\n")
    code[4] += "// comment"
    code = "\n".join(code)
    with mockproject._path.joinpath("contracts/BaseFoo.sol").open("w") as fp:
        fp.write(code)

    mockproject.load()
    assert sorted(mockproject._compile.call_args[0][0]) == [
        "contracts/BaseFoo.sol",
        "contracts/Foo.sol",
    ]
