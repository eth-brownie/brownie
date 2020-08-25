import pytest

# unconventional-but-compilable contract sources that should not cause issues


@pytest.mark.parametrize("minor", (4, 5, 6))
def test_blank(newproject, minor):
    with newproject._path.joinpath("contracts/Blank.sol").open("w") as fp:
        fp.write("pragma solidity ^0.{}.0; contract Blank {{}}".format(minor))
    newproject.load()


@pytest.mark.parametrize("minor", (4, 5, 6))
def test_only_events(newproject, minor):
    source = """
pragma solidity ^0.{}.0;

contract OnlyEvents {{
    event Transfer(address from, address to, uint256 value);
    event Approval(address owner, address spender, uint256 value);
}}""".format(
        minor
    )
    with newproject._path.joinpath("contracts/OnlyEvents.sol").open("w") as fp:
        fp.write(source)
    newproject.load()


def test_vyper_external_call(newproject):
    source = """
# @version 0.2.4
from vyper.interfaces import ERC721
@external
def interfaceTest():
    ERC721(msg.sender).safeTransferFrom(msg.sender, self, 1, b"")
    """
    with newproject._path.joinpath("contracts/Vyper.vy").open("w") as fp:
        fp.write(source)
    newproject.load()
