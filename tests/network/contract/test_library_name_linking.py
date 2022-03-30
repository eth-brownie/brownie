"""
Test following edge case of library name during linking into project:
- name to long, greater than 36 character
- name containing underscore `_` on beging and in middle
- name ending with underscores `_`
"""
import pytest

from brownie import compile_source

SOURCE = """pragma solidity ^0.8.0;

library LibName {

    function linkMethod(uint a, uint b) public pure returns (uint) {
        return a * b;
    }
}

contract Unlinked {

    function callLibrary(uint amount, uint multiple) external returns (uint) {
        return LibName.linkMethod(amount, multiple);
    }
}
"""


def test_library_name_too_long():
    name = 12 * "Lib" + "B"
    with pytest.raises(AssertionError) as error:
        compile_source(SOURCE.replace("LibName", name))
    assert str(error.value).startswith(f"Library name '{name}' is too long")


def test_library_name_ends_for_underscores():
    for name in ("__lib__name_", "__LibName__", "lib___name____"):
        with pytest.raises(AssertionError) as error:
            compile_source(SOURCE.replace("LibName", name))
        assert str(error.value).startswith(f"Library name '{name}' cannot end with '_'")


@pytest.mark.parametrize("lib_name", ["__lib__name", "__LibName", "lib___name"])
def test_library_name_with_underscore(accounts, lib_name):
    compiled = compile_source(SOURCE.replace("LibName", lib_name))
    lib = accounts[0].deploy(compiled[lib_name], silent=True)
    contract = accounts[0].deploy(compiled["Unlinked"], silent=True)
    assert lib.address[2:].lower() in contract.bytecode
