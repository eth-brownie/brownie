#!/usr/bin/python3

import pytest
from web3.exceptions import Web3RPCError

from brownie.exceptions import VirtualMachineError
from brownie.network.middlewares.catch_tx_revert import TxRevertCatcherMiddleware
from brownie.network.middlewares.ganache7 import Ganache7MiddleWare

TXID = "0x" + "12" * 32


def _tx_rpc_error_payload():
    return {
        "message": "VM Exception while processing transaction: revert boom",
        "data": {
            "hash": TXID,
            "message": "revert",
            "programCounter": 12,
            "reason": "boom",
        },
    }


@pytest.mark.parametrize(
    "make_exc",
    [
        lambda payload: Web3RPCError("execution reverted", rpc_response={"error": payload}),
        lambda payload: ValueError({"error": payload}),
    ],
)
def test_virtual_machine_error_normalizes_web3_v7_rpc_payloads(make_exc):
    exc = make_exc(_tx_rpc_error_payload())

    error = VirtualMachineError(exc)

    assert error.txid == TXID
    assert error.message == "VM Exception while processing transaction: revert boom"
    assert error.revert_type == "revert"
    assert error.pc == 11
    assert error.revert_msg == "boom"


@pytest.mark.parametrize("method", ["eth_call", "eth_estimateGas"])
def test_tx_revert_catcher_converts_web3_v7_rpc_errors(method):
    rpc_response = {"error": {"message": "execution reverted", "data": "0x"}}

    def make_request(method, params):
        raise Web3RPCError("execution reverted", rpc_response=rpc_response)

    with pytest.raises(ValueError) as exc:
        TxRevertCatcherMiddleware().process_request(make_request, method, [])

    assert exc.value.args[0] == rpc_response["error"]


def test_ganache7_middleware_normalizes_raised_web3_v7_rpc_errors():
    rpc_response = {"error": _tx_rpc_error_payload()}

    def make_request(method, params):
        raise Web3RPCError("execution reverted", rpc_response=rpc_response)

    result = Ganache7MiddleWare().process_request(make_request, "eth_sendTransaction", [])

    assert result["error"]["data"] == {
        TXID: {
            "error": "revert",
            "program_counter": 12,
            "reason": "boom",
        }
    }
