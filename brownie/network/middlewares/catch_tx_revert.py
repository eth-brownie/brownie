from typing import Callable, Dict, List, Optional

from web3 import Web3

from brownie.network.middlewares import BrownieMiddlewareABC


class TxRevertCatcherMiddleware(BrownieMiddlewareABC):

    """
    Middleware to handle reverting transactions, bypasses web3 error formatting.

    As of web3.py version 5.13.0, a new error formatting middleware was added by default
    `raise_solidity_error_on_revert` which when a `eth_call` or `eth_estimateGas` tx
    raises a `ContractLogicError` instead of providing us with an RPCError dictionary.
    """

    @classmethod
    def get_layer(cls, w3: Web3, network_type: str) -> Optional[int]:
        return -1

    def process_request(self, make_request: Callable, method: str, params: List) -> Dict:
        """Raise a ValueError when RPC.eth_call or RPC.eth_estimateGas errors."""
        result = make_request(method, params)
        if method in ("eth_call", "eth_estimateGas"):
            if "error" in result:
                raise ValueError(result["error"])
        return result
