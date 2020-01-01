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

    function requireBranches(uint i, bool a, bool b, bool c, bool d) public returns (bool) {
        if (i == 1) {
            require(a);
            require(a, "error");
        }
        if (i == 2) {
            require(!a);
            require(!a, "error");
        }
        if (i == 3) {
            require(a || b);
            require(a || b, "error");
            require(a && b);
            require(a && b, "error");
        }
        if (i == 4) {
            require(!a || !b);
            require(!a || !b, "error");
            require(!a && !b);
            require(!a && !b, "error");
        }
        if (i == 5) {
            require(a || b || c);
            require(a || b || c, "error");
            require(a && b && c);
            require(a && b && c, "error");
        }
        if (i == 6) {
            require(!a || !b || !c);
            require(!a || !b || !c, "error");
            require(!a && !b && !c);
            require(!a && !b && !c, "error");
        }
        if (i == 7) {
            require((a && b) || (c && d));
            require((a && b) || (c && d), "error");
            require((a || b) && (c || d));
            require((a || b) && (c || d), "error");
        }
        if (i == 8) {
            require((!a && !b) || (!c && !d));
            require((!a && !b) || (!c && !d), "error");
            require((!a || !b) && (!c || !d));
            require((!a || !b) && (!c || !d), "error");
        }
    }

    function terneryBranches(uint i, bool a, bool b, bool c, bool d) public returns (bool) {
        uint x;
        if (i == 1) {
            x = a ? 1 : 2;
            x = !a ? 1 : 2;
        }
        if (i == 2) {
            x = (a && b) ? 1 : 2;
            x = (a || b) ? 1 : 2;
        }
        if (i == 3) {
            x = (!a && !b) ? 1 : 2;
            x = (!a || !b) ? 1 : 2;
        }
        if (i == 4) {
            x = (a && b && c) ? 1 : 2;
            x = (a || b || c) ? 1 : 2;
        }
        if (i == 5) {
            x = (!a && !b && !c) ? 1 : 2;
            x = (!a || !b || !c) ? 1 : 2;
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

    uint256[3] x;

    function invalidOpcodes(uint a, uint b) external returns (uint c) {
        assert (a > 0);
        assert (a + b > 1); // dev: foobar
        c = x[a];
        c = a / b;
    }

    function modulusByZero(uint a, uint b) external returns (uint) {
        return a % b;
    }

}
