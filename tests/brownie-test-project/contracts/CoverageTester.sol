pragma solidity ^0.5.0;

contract CoverageTester {

    function ifBranches(bool a, bool b, bool c, bool d) public returns (bool) {
        if (a && b && c && d) return true;
        if ((a && b) || (c && d)) return true;
        if (a || b || c || d) {
            if (a && (c || d)) return true;
        } else {
            return false;
        }
        return true;
    }

    function requireBranches(bool a, bool b, bool c, bool d) public returns (bool) {
        require(a || b || c || d);
        require((a || b) && (c || d));
        require((a && c) || d);
        return true;
    }

    function terneryBranches(bool a, bool b) public returns (bool) {
        uint x = (a ? 1 : 2);
        uint y = (a && b ? 1 : 2);
        uint z = (a || b ? 1 : 2);
        return true;
    }
}