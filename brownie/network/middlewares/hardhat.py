from typing import Callable, Dict, List, Optional

from web3 import Web3

from brownie.network.middlewares import BrownieMiddlewareABC


class HardhatMiddleWare(BrownieMiddlewareABC):
    @classmethod
    def get_layer(cls, w3: Web3, network_type: str) -> Optional[int]:
        if w3.clientVersion.lower().startswith("hardhat"):
            return -100
        else:
            return None

    def process_request(self, make_request: Callable, method: str, params: List) -> Dict:
        result = make_request(method, params)

        # modify Hardhat transaction error to mimick the format that Ganache uses
        if method in ("eth_call", "eth_sendTransaction") and "error" in result:
            message = result["error"]["message"]
            if message.startswith("Error: VM Exception") or message.startswith(
                "Error: Transaction reverted"
            ):
                if method == "eth_call":
                    # ganache returns a txid even on a failed eth_call, which is weird,
                    # but we still mimick it here for the sake of consistency
                    txid = "0x"
                else:
                    txid = result["error"]["data"]["txHash"]
                data: Dict = {}
                result["error"]["data"] = {txid: data}
                message = message.split(": ", maxsplit=1)[-1]
                if message == "Transaction reverted without a reason":
                    data.update({"error": "revert", "reason": None})
                elif message.startswith("revert"):
                    data.update({"error": "revert", "reason": message[7:]})
                else:
                    data["error"] = message
        return result
