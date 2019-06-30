pragma solidity ^0.5.0;

interface TokenInterface {

    event Transfer(address from, address to, uint256 value);
    event Approval(address owner, address spender, uint256 value);

    function balanceOf(address) external view returns (uint256);
    function allowance(address, address) external view returns (uint256);
    function approve(address, uint256) external returns (bool);
    function transfer(address, uint256) external returns (bool);
    function transferFrom(address, address, uint256) external returns (bool);

}

contract TokenABC {

    string public symbol;
    string public  name;
    uint256 public decimals;
    uint256 public totalSupply;

    event Transfer(address from, address to, uint256 value);
    event Approval(address owner, address spender, uint256 value);

    function () external payable;

    function balanceOf(address _owner) public view returns (uint256);

    function allowance(address _owner, address _spender) public view returns (uint256);

    function approve(address _spender, uint256 _value) public returns (bool);

    function transfer(address _to, uint256 _value) public returns (bool);

    function transferFrom(address _from, address _to, uint256 _value) public returns (bool);

}

contract Blank {}

contract OnlyEvents {
    event Transfer(address from, address to, uint256 value);
    event Approval(address owner, address spender, uint256 value);
}