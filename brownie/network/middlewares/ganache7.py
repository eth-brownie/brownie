from typing import Any, Callable, Dict, Optional, Sequence, final

from web3 import Web3
from web3.types import RPCEndpoint

from brownie.network.middlewares import BrownieMiddlewareABC


@final
class Ganache7MiddleWare(BrownieMiddlewareABC):
    @classmethod
    def get_layer(cls, w3: Web3, network_type: str) -> Optional[int]:
        return -100 if w3.client_version.lower().startswith("ganache/v7") else None

    def process_request(
        self,
        make_request: Callable,
        method: RPCEndpoint,
        params: Sequence[Any],
    ) -> Dict[str, Any]:
        result = make_request(method, params)

        # reformat failed eth_call / eth_sendTransaction output to mimick that of Ganache 6.x
        # yes, this is hacky and awful and in the future we should stop supporting
        # the older version of ganache. but doing so will cause unexpected issues
        # in projects that are still pinned to the old verion, so for now we support
        # both and simply raise a warning of a pending deprecation.
        data: dict
        error: dict
        if (
            method in {"eth_sendTransaction", "eth_sendRawTransaction"}
            and "error" in result
            and "data" in (error := result["error"])
        ):
            data = error["data"]
            data["error"] = data.pop("message")
            data["program_counter"] = data.pop("programCounter")
            error["data"] = {data.pop("hash"): data}

        if method == "eth_call" and "error" in result:
            error = result["error"]
            if error.get("message", "").startswith("VM Exception"):
                # "VM Exception while processing transaction: {reason} {message}"
                msg: str = error["message"]
                msg = msg.split(": ", maxsplit=1)[-1]
                if msg.startswith("revert"):
                    data = {"error": "revert", "reason": error["data"]}
                else:
                    data = {"error": msg, "reason": None}
                error["data"] = {"0x": data}

        return result
