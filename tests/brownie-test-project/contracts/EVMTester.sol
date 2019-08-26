pragma solidity >=0.4.25;

contract EVMTester {

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

    function revertStrings(uint a) external returns (bool) {
        require (a != 0, "zero");
        require (a != 1); // dev: one
        require (a != 2, "two"); // dev: error
        require (a != 3); // error
        if (a != 31337) {
            return true;
        }
        revert(); // dev: great job
    }

}
