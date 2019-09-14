pragma solidity >=0.4.22;

contract EVMTester {

    function ifBranches(uint i, bool a, bool b, bool c, bool d) public returns (bool) {
        if (i == 1) {
            if (a) return true;
            if (!a) return true;
        }
        if (i == 2) {
            if (a && b) return true;
            if (a || b) return true;
        }
        if (i == 3) {
            if (!a && !b) return true;
            if (!a || !b) return true;
        }
        if (i == 4) {
            if (a && b && c) return true;
            if (a || b || c) return true;
        }
        if (i == 5) {
            if (!a && !b && !c) return true;
            if (!a || !b || !c) return true;
        }
        if (i == 6) {
            if ((a && b) || (c && d)) return true;
            if ((a || b) && (c || d)) return true;
        }
        if (i == 7) {
            if ((!a && !b) || (!c && !d)) return true;
            if ((!a || !b) && (!c || !d)) return true;
        }
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
