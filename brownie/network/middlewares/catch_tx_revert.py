from typing import Any, Callable, Dict, Optional, Sequence, final

from web3 import Web3
from web3.types import RPCEndpoint

from brownie.network.middlewares import BrownieMiddlewareABC


@final
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

    def process_request(
        self,
        make_request: Callable,
        method: RPCEndpoint,
        params: Sequence[Any],
    ) -> Dict[str, Any]:
        """Raise a ValueError when RPC.eth_call or RPC.eth_estimateGas errors."""
        result = make_request(method, params)
        if method in {"eth_call", "eth_estimateGas"} and "error" in result:
            raise ValueError(result["error"])
        return result
