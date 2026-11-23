#!/usr/bin/python3

import pytest
from web3.exceptions import Web3RPCError

from brownie.exceptions import VirtualMachineError
from brownie.network.middlewares.catch_tx_revert import TxRevertCatcherMiddleware
from brownie.network.middlewares.ganache7 import Ganache7MiddleWare
from brownie.network.web3 import Web3

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


def _brownie_error_payload():
    return {
        "message": "VM Exception while processing transaction: revert boom",
        "data": {
            TXID: {
                "error": "revert",
                "program_counter": 12,
                "reason": "boom",
            }
        },
    }


def test_virtual_machine_error_normalizes_web3_v7_rpc_payloads():
    exc = Web3RPCError("execution reverted", rpc_response={"error": _tx_rpc_error_payload()})

    error = VirtualMachineError(exc)

    assert error.txid == TXID
    assert error.message == "VM Exception while processing transaction: revert boom"
    assert error.revert_type == "revert"
    assert error.pc == 11
    assert error.revert_msg == "boom"


def test_virtual_machine_error_keeps_brownie_value_error_payloads():
    error = VirtualMachineError(ValueError(_brownie_error_payload()))

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

    middleware = Web3()._build_middleware(TxRevertCatcherMiddleware)[1]
    with pytest.raises(ValueError) as exc:
        middleware.process_request(make_request, method, [])

    assert exc.value.args[0] == rpc_response["error"]


def test_tx_revert_catcher_reraises_web3_v7_rpc_errors_for_other_methods():
    rpc_error = Web3RPCError(
        "execution reverted",
        rpc_response={"error": {"message": "execution reverted", "data": "0x"}},
    )

    def make_request(method, params):
        raise rpc_error

    middleware = Web3()._build_middleware(TxRevertCatcherMiddleware)[1]
    with pytest.raises(Web3RPCError) as exc:
        middleware.process_request(make_request, "eth_sendTransaction", [])

    assert exc.value is rpc_error


def test_ganache7_middleware_normalizes_raised_web3_v7_rpc_errors():
    rpc_response = {"error": _tx_rpc_error_payload()}

    def make_request(method, params):
        raise Web3RPCError("execution reverted", rpc_response=rpc_response)

    middleware = Web3()._build_middleware(Ganache7MiddleWare)[1]
    result = middleware.process_request(make_request, "eth_sendTransaction", [])

    assert result["error"]["data"] == {
        TXID: {
            "error": "revert",
            "program_counter": 12,
            "reason": "boom",
        }
    }


def test_ganache7_middleware_reraises_web3_v7_rpc_errors_without_response():
    rpc_error = Web3RPCError("execution reverted")

    def make_request(method, params):
        raise rpc_error

    middleware = Web3()._build_middleware(Ganache7MiddleWare)[1]
    with pytest.raises(Web3RPCError) as exc:
        middleware.process_request(make_request, "eth_sendTransaction", [])

    assert exc.value is rpc_error
