pragma solidity ^0.5.0;

contract ExternalCallTester {

    function callAnother(Other other, uint a) external returns (bool) {
        bool ok = other.getCalled(a);
        return ok;
    }

    function doNotCall(Other other) external returns (bool) {
        return true;
    }

}

contract Other {

    function getCalled(uint a) external returns (bool) {
        require(a > 2);
        return true;
    }
}