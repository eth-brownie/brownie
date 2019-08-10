pragma solidity ^0.5.0;
pragma experimental ABIEncoderV2;

import "./SafeMath.sol";

/** @notice This is the main contract used to test Brownie functionality */
contract BrownieTester {

    using SafeMath for uint;

    address payable public owner;

    struct Nested {
        string a;
        bytes32 b;
    }

    struct Base {
        string str;
        address addr;
        Nested nested;
    }

    mapping (address => Base) testMap;

    event TupleEvent(address addr, Base base);
    event Debug(uint a);

    constructor (bool success) public {
        require(success);
        owner = msg.sender;
    }

    function () external payable {
        require(msg.value >= 1 ether);
        emit Debug(31337);
    }

    function sendEth() external returns (bool) {
        owner.transfer(address(this).balance);
        return true;
    }

    function receiveEth() external payable returns (bool) {
        return true;
    }

    function doNothing() external returns (bool) {
        return true;
    }

    function revertStrings(uint a) external returns (bool) {
        emit Debug(a);
        require (a != 0, "zero");
        require (a != 1); // dev: one
        require (a != 2, "two"); // dev: error
        require (a != 3); // error
        if (a != 31337) {
            return true;
        }
        revert(); // dev: great job
    }

    function setTuple(Base memory _base) public {
        testMap[_base.addr] = _base;
        emit TupleEvent(_base.addr, _base);
    }

    function getTuple(address _addr) public view returns (Base memory) {
        return testMap[_addr];
    }

    function manyValues(
        uint a,
        bool[] calldata b,
        address c,
        bytes32[2][] calldata d
    )
        external
        view
        returns (uint _num, bool[] memory _bool, address _addr, bytes32[2][] memory _bytes)
    {
        return (a, b, c, d);
    }

    function makeExternalCall(ExternalCallTester other, uint a) external returns (bool) {
        bool ok = other.getCalled(a.sub(2));
        return ok;
    }

}


contract ExternalCallTester {

    function getCalled(uint a) external returns (bool) {
        require(a > 2);
        return true;
    }
}
