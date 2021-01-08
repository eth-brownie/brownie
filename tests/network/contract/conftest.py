import pytest

@pytest.fixture
def brownie_tester_flat():
    yield """// SPDX-License-Identifier: NONE

pragma solidity 0.5.17;
pragma experimental ABIEncoderV2;



// Part: BrownieTester

pragma solidity ^0.5.0;
pragma experimental ABIEncoderV2;

import "./SafeMath.sol";

/** @notice This is the main contract used to test Brownie functionality */
contract BrownieTester {

    using SafeMath for uint;

    address payable public owner;
    uint256 num;

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
    event IndexedEvent(string indexed str, uint256 indexed num);

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

    function emitEvents(string calldata str, uint256 num) external returns (bool) {
        emit Debug(num);
        emit IndexedEvent(str, num);
        emit Debug(num + 2);
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

    function setNum(uint _num) external returns (bool) {
        num = _num;
        return true;
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

    function useSafeMath(uint a, uint b) external returns (uint) {
        uint c = a.mul(b);
        return c;
    }

    function makeExternalCall(ExternalCallTester other, uint a) external returns (bool) {
        bool ok = other.getCalled(a);
        return ok;
    }

    function makeInternalCalls(bool callPublic, bool callPrivate) external returns (bool) {
        if (callPublic) {
            getCalled(0);
        }
        if (callPrivate) {
            _getCalled(0);
        }
        return true;
    }

    function getCalled(uint a) public returns (bool) {
        return _getCalled(a);
    }

    function _getCalled(uint a) internal returns (bool) {
        return false;
    }

}

// Part: SafeMath

library SafeMath {
    function add(uint a, uint b) internal pure returns (uint c) {
        c = a + b;
        require(c >= a);
    }
    function sub(uint a, uint b) internal pure returns (uint c) {
        require(b <= a);
        c = a - b;
    }
    function mul(uint a, uint b) internal pure returns (uint c) {
        c = a * b;
        require(a == 0 || c / a == b);
    }
    function div(uint a, uint b) internal pure returns (uint c) {
        require(b > 0);
        c = a / b;
    }
}

// Part: ExternalCallTester

contract ExternalCallTester {

    function getCalled(uint a) external returns (bool) {
        if (a > 2) {
            return true;
        }
        revert(); // dev: should jump to a revert
    }

    function makeExternalCall(BrownieTester other, uint a) external returns (bool) {
        other.revertStrings(a);
        return true;
    }

}

// File: BrownieTester.sol

pragma solidity ^0.5.0;
pragma experimental ABIEncoderV2;

import "./SafeMath.sol";

/** @notice This is the main contract used to test Brownie functionality */
contract BrownieTester {

    using SafeMath for uint;

    address payable public owner;
    uint256 num;

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
    event IndexedEvent(string indexed str, uint256 indexed num);

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

    function emitEvents(string calldata str, uint256 num) external returns (bool) {
        emit Debug(num);
        emit IndexedEvent(str, num);
        emit Debug(num + 2);
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

    function setNum(uint _num) external returns (bool) {
        num = _num;
        return true;
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

    function useSafeMath(uint a, uint b) external returns (uint) {
        uint c = a.mul(b);
        return c;
    }

    function makeExternalCall(ExternalCallTester other, uint a) external returns (bool) {
        bool ok = other.getCalled(a);
        return ok;
    }

    function makeInternalCalls(bool callPublic, bool callPrivate) external returns (bool) {
        if (callPublic) {
            getCalled(0);
        }
        if (callPrivate) {
            _getCalled(0);
        }
        return true;
    }

    function getCalled(uint a) public returns (bool) {
        return _getCalled(a);
    }

    function _getCalled(uint a) internal returns (bool) {
        return false;
    }

}
"""