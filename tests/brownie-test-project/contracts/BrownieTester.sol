pragma solidity ^0.5.0;

library UnlinkedLib {

    function linkMethod(
        uint256 _value,
        uint256 _multiplier
    )
        public
        pure
        returns (uint256)
    {
        return _value * _multiplier;
    }
}

contract BrownieTester {

    address payable owner;

    event Debug(uint a);

    constructor () public {
        owner = msg.sender;
    }

    function receiveEth() external payable returns (bool) {
        return true;
    }

    function sendEth() external returns (bool) {
        owner.transfer(address(this).balance);
        return true;
    }

    function testLibraryLink(uint amount, uint multiple) external view returns (uint) {
        return UnlinkedLib.linkMethod(amount, multiple);
    }

    function testRevertStrings(uint a) external returns (bool) {
        emit Debug(a);
        require (a != 0, "zero");
        require (a != 1); // dev: one
        require (a != 2, "two"); // dev: error
        require (a != 3); // error
        return true;
    }

    function doNothing() external returns (bool) {
        return true;
    }

}
