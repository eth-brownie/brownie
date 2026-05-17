from collections.abc import Callable, Sequence
from typing import Any, final

from web3 import Web3
from web3.exceptions import ContractLogicError, Web3RPCError
from web3.types import RPCEndpoint

from brownie.network.middlewares import BrownieMiddlewareABC


@final
class TxRevertCatcherMiddleware(BrownieMiddlewareABC):
    """
    Middleware to handle reverting transactions, bypasses web3 error formatting.

    Modern web3.py can raise `ContractLogicError` or `Web3RPCError` for `eth_call`
    and `eth_estimateGas`, instead of returning an RPC error dictionary.
    """

    @classmethod
    def get_layer(cls, w3: Web3, network_type: str) -> int | None:
        return -1

    def process_request(
        self,
        make_request: Callable,
        method: RPCEndpoint,
        params: Sequence[Any],
    ) -> dict[str, Any]:
        """Raise a ValueError when RPC.eth_call or RPC.eth_estimateGas errors."""
        try:
            result = make_request(method, params)
        except (ContractLogicError, Web3RPCError) as exc:
            if method not in {"eth_call", "eth_estimateGas"}:
                raise
            if isinstance(exc, Web3RPCError):
                if exc.rpc_response is None:
                    raise
                raise ValueError(exc.rpc_response["error"]) from None
            raise ValueError(exc.args[0] if exc.args else exc) from None
        if method in {"eth_call", "eth_estimateGas"} and "error" in result:
            raise ValueError(result["error"])
        return result
