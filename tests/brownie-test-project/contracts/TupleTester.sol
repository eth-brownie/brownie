pragma solidity ^0.4.24;
pragma experimental ABIEncoderV2;

contract TupleTester {

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


    function setTuple(Base _base) public {
        testMap[_base.addr] = _base;
        emit TupleEvent(_base.addr, _base);
    }

    function getTuple(address _addr) constant public returns (Base) {
        return testMap[_addr];
    }
}