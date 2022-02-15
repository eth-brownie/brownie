#!/usr/bin/python3

import pytest

from brownie.exceptions import VirtualMachineError
from brownie.project import compile_source

REVERT_FUNCTIONS_NO_INPUT = [
    """
    function foo () external returns (bool) {{
        {}; // dev: yuss
    }}""",
    """
    function foo () external returns (bool) {{
        uint b = 33;
        {}; // dev: yuss
    }}""",
]

REVERT_FUNCTIONS_INPUT = [
    """
    function foo (uint a) external returns (bool) {{
        if (a < 3) {{
            return true;
        }}
        {}; // dev: yuss
    }}""",
    """
    function foo (uint a) external returns (bool) {{
        require(a >= 3);
        {}; // dev: yuss
    }}""",
    """
    function foo (uint a) external {{
        require(a >= 3);
        {}; // dev: yuss
    }}""",
]


@pytest.mark.parametrize("expr", ["revert()", "require(false)"])
@pytest.mark.parametrize("func", REVERT_FUNCTIONS_NO_INPUT)
def test_final_stmt_revert_no_input_no_msg(console_mode, evmtester, accounts, expr, func):

    func = func.format(expr)
    code = f"""
pragma solidity >=0.4.22;
contract Foo {{
    {func}
}}
    """

    contract = compile_source(code).Foo.deploy({"from": accounts[0]})
    tx = contract.foo()
    assert tx.revert_msg == "dev: yuss"
    assert tx.dev_revert_msg == "dev: yuss"


@pytest.mark.parametrize("expr", ["revert('foo')", "require(false, 'foo')"])
@pytest.mark.parametrize("func", REVERT_FUNCTIONS_NO_INPUT)
def test_final_stmt_revert_no_input(console_mode, evmtester, accounts, expr, func):

    func = func.format(expr)
    code = f"""
pragma solidity >=0.4.22;
contract Foo {{
    {func}
}}
    """

    contract = compile_source(code).Foo.deploy({"from": accounts[0]})
    tx = contract.foo()
    assert tx.revert_msg == "foo"
    assert tx.dev_revert_msg == "dev: yuss"


@pytest.mark.parametrize("expr", ["revert()", "require(false)"])
@pytest.mark.parametrize("func", REVERT_FUNCTIONS_INPUT)
def test_final_stmt_revert_input_no_msg(console_mode, evmtester, accounts, expr, func):

    func = func.format(expr)
    code = f"""
pragma solidity >=0.4.22;
contract Foo {{
    {func}
}}
    """

    contract = compile_source(code).Foo.deploy({"from": accounts[0]})
    tx = contract.foo(4)
    assert tx.revert_msg == "dev: yuss"


@pytest.mark.parametrize("expr", ["revert('foo')", "require(false, 'foo')"])
@pytest.mark.parametrize("func", REVERT_FUNCTIONS_INPUT)
def test_final_stmt_revert_input(console_mode, evmtester, accounts, expr, func):

    func = func.format(expr)
    code = f"""
pragma solidity >=0.4.22;
contract Foo {{
    {func}
}}
    """

    contract = compile_source(code).Foo.deploy({"from": accounts[0]})
    tx = contract.foo(4)
    assert tx.revert_msg == "foo"
    assert tx.dev_revert_msg == "dev: yuss"


def test_revert_msg_via_jump(ext_tester, console_mode):
    tx = ext_tester.getCalled(2)
    assert tx.revert_msg == "dev: should jump to a revert"


def test_solidity_revert_msg(evmtester, console_mode):
    tx = evmtester.revertStrings(0)
    assert tx.revert_msg == "zero"
    assert tx.dev_revert_msg is None
    tx = evmtester.revertStrings(1)
    assert tx.revert_msg == "dev: one"
    assert tx.dev_revert_msg == "dev: one"
    tx = evmtester.revertStrings(2)
    assert tx.revert_msg == "two"
    assert tx.dev_revert_msg == "dev: error"
    tx = evmtester.revertStrings(3)
    assert tx.revert_msg == ""
    assert tx.dev_revert_msg is None
    tx = evmtester.revertStrings(31337)
    assert tx.revert_msg == "dev: great job"
    assert tx.dev_revert_msg == "dev: great job"


def test_vyper_revert_msg(vypertester, console_mode):
    tx = vypertester.revertStrings(0)
    assert tx.revert_msg == "zero"
    assert tx.dev_revert_msg is None
    tx = vypertester.revertStrings(1)
    assert tx.revert_msg == "dev: one"
    assert tx.dev_revert_msg == "dev: one"
    tx = vypertester.revertStrings(2)
    assert tx.revert_msg == "two"
    assert tx.dev_revert_msg == "dev: error"
    tx = vypertester.revertStrings(3)
    assert tx.revert_msg == ""
    assert tx.dev_revert_msg is None
    tx = vypertester.revertStrings(4)
    assert tx.revert_msg == "dev: such modifiable, wow"
    assert tx.dev_revert_msg == "dev: such modifiable, wow"
    tx = vypertester.revertStrings(31337)
    assert tx.revert_msg == "awesome show"
    assert tx.dev_revert_msg == "dev: great job"


def test_nonpayable(tester, evmtester, console_mode):
    tx = evmtester.revertStrings(0, {"value": 100})
    assert tx.revert_msg == "Cannot send ether to nonpayable function"
    tx = tester.doNothing({"value": 100})
    assert tx.revert_msg == "Cannot send ether to nonpayable function"


def test_solidity_invalid_opcodes(evmtester):
    with pytest.raises(VirtualMachineError) as exc:
        evmtester.invalidOpcodes(0, 0)
    assert exc.value.revert_msg in ("Failed assertion", "invalid opcode")
    with pytest.raises(VirtualMachineError) as exc:
        evmtester.invalidOpcodes(1, 0)
    assert exc.value.revert_msg == "dev: foobar"
    with pytest.raises(VirtualMachineError) as exc:
        evmtester.invalidOpcodes(3, 3)
    assert exc.value.revert_msg == "Index out of range"
    with pytest.raises(VirtualMachineError) as exc:
        evmtester.invalidOpcodes(2, 0)
    assert exc.value.revert_msg in ("Division or modulo by zero", "Division by zero")
    with pytest.raises(VirtualMachineError) as exc:
        evmtester.modulusByZero(2, 0)
    assert exc.value.revert_msg in ("Division or modulo by zero", "Modulus by zero")


def test_vyper_revert_reasons(vypertester, console_mode):
    tx = vypertester.outOfBounds(6, 31337)
    assert tx.revert_msg == "Index out of range"
    tx = vypertester.overflow(6, 2**255)
    assert tx.revert_msg == "Integer overflow"
    tx = vypertester.underflow(6, 8)
    assert tx.revert_msg == "Integer underflow"
    tx = vypertester.zeroDivision(6, 0)
    assert tx.revert_msg == "Division by zero"
    tx = vypertester.zeroModulo(6, 0)
    assert tx.revert_msg == "Modulo by zero"
    tx = vypertester.overflow(0, 0, {"value": 31337})
    assert tx.revert_msg == "Cannot send ether to nonpayable function"


def test_deployment_size_limit(accounts, console_mode):
    code = f"""
# @version 0.2.4

@external
def baz():
    assert msg.sender != ZERO_ADDRESS, '{'blah'*10000}'
    """
    tx = compile_source(code, vyper_version="0.2.4").Vyper.deploy({"from": accounts[0]})
    assert tx.revert_msg == "exceeds EIP-170 size limit"
