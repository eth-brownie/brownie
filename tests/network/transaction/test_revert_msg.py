#!/usr/bin/python3

import pytest

from brownie.exceptions import VirtualMachineError
from brownie.project import compile_source


def test_revert_msg_via_jump(ext_tester, console_mode):
    tx = ext_tester.getCalled(2)
    assert tx.revert_msg == "dev: should jump to a revert"


def test_solidity_revert_msg(evmtester, console_mode):
    tx = evmtester.revertStrings(0)
    assert tx.revert_msg == "zero"
    tx = evmtester.revertStrings(1)
    assert tx.revert_msg == "dev: one"
    tx = evmtester.revertStrings(2)
    assert tx.revert_msg == "two"
    tx = evmtester.revertStrings(3)
    assert tx.revert_msg == ""
    tx = evmtester.revertStrings(31337)
    assert tx.revert_msg == "dev: great job"


def test_vyper_revert_msg(vypertester, console_mode):
    tx = vypertester.revertStrings(0)
    assert tx.revert_msg == "zero"
    tx = vypertester.revertStrings(1)
    assert tx.revert_msg == "dev: one"
    tx = vypertester.revertStrings(2)
    assert tx.revert_msg == "two"
    tx = vypertester.revertStrings(3)
    assert tx.revert_msg == ""
    tx = vypertester.revertStrings(4)
    assert tx.revert_msg == "dev: such modifiable, wow"
    tx = vypertester.revertStrings(31337)
    assert tx.revert_msg == "awesome show"


def test_nonpayable(tester, evmtester, console_mode):
    tx = evmtester.revertStrings(0, {"value": 100})
    assert tx.revert_msg == "Cannot send ether to nonpayable function"
    tx = tester.doNothing({"value": 100})
    assert tx.revert_msg == "Cannot send ether to nonpayable function"


def test_solidity_invalid_opcodes(evmtester):
    with pytest.raises(VirtualMachineError) as exc:
        evmtester.invalidOpcodes(0, 0)
    assert exc.value.revert_msg == "invalid opcode"
    with pytest.raises(VirtualMachineError) as exc:
        evmtester.invalidOpcodes(1, 0)
    assert exc.value.revert_msg == "dev: foobar"
    with pytest.raises(VirtualMachineError) as exc:
        evmtester.invalidOpcodes(3, 3)
    assert exc.value.revert_msg == "Index out of range"
    with pytest.raises(VirtualMachineError) as exc:
        evmtester.invalidOpcodes(2, 0)
    assert exc.value.revert_msg == "Division by zero"
    with pytest.raises(VirtualMachineError) as exc:
        evmtester.modulusByZero(2, 0)
    assert exc.value.revert_msg == "Modulus by zero"


def test_vyper_revert_reasons(vypertester, console_mode):
    tx = vypertester.outOfBounds(6, 31337)
    assert tx.revert_msg == "Index out of range"
    tx = vypertester.overflow(6, 2 ** 255)
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
    code = f"@public\ndef baz():\n    assert msg.sender != ZERO_ADDRESS, '{'blah'*10000}'"
    tx = compile_source(code).Vyper.deploy({"from": accounts[0]})
    assert tx.revert_msg == "exceeds EIP-170 size limit"
