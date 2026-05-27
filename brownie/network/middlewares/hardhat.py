from typing import Any, TypedDict, cast, final

from typing_extensions import NotRequired
from web3 import Web3
from web3.types import MakeRequestFn, RPCEndpoint, RPCResponse

from brownie._c_constants import regex_findall
from brownie.network.middlewares import BrownieMiddlewareABC


LegacyGanacheErrorData = TypedDict(
    "LegacyGanacheErrorData",
    {
        "error": str,
        "program_counter": int | None,
        "reason": str | None,
        "result": str,
        "return": str,
    },
    total=False,
)


class HardhatTxHashErrorData(TypedDict):
    txHash: str


class _HardhatRPCError(TypedDict):
    message: str
    data: NotRequired[HardhatTxHashErrorData | dict[str, LegacyGanacheErrorData]]


@final
class HardhatMiddleWare(BrownieMiddlewareABC):
    @classmethod
    def get_layer(cls, w3: Web3, network_type: str) -> int | None:
        if w3.client_version.lower().startswith("hardhat"):
            return -100
        else:
            return None

    def process_request(
        self,
        make_request: MakeRequestFn,
        method: RPCEndpoint,
        params: Any,
    ) -> RPCResponse:
        result = make_request(method, params)

        # modify Hardhat transaction error to mimic the format that Ganache uses
        if (
            method in {"eth_call", "eth_sendTransaction", "eth_sendRawTransaction"}
            and "error" in result
        ):
            error = cast(_HardhatRPCError, result["error"])
            message = error["message"]
            if message.startswith("Error: VM Exception") or message.startswith(
                "Error: Transaction reverted"
            ):
                if method == "eth_call":
                    # ganache returns a txid even on a failed eth_call, which is weird,
                    # but we still mimic it here for the sake of consistency
                    txid = "0x"
                else:
                    provider_data = cast(HardhatTxHashErrorData, error["data"])
                    txid = provider_data["txHash"]
                data: LegacyGanacheErrorData = {}
                normalized_data: dict[str, LegacyGanacheErrorData] = {txid: data}
                error["data"] = normalized_data
                message = message.split(": ", maxsplit=1)[-1]
                if message == "Transaction reverted without a reason":
                    data["error"] = "revert"
                    data["reason"] = None
                elif message.startswith("revert"):
                    data["error"] = "revert"
                    data["reason"] = message[7:]
                elif "reverted with reason string '" in message:
                    data["error"] = "revert"
                    data["reason"] = regex_findall(".*?'(.*)'$", message)[0]
                elif "reverted with an unrecognized custom error" in message:
                    message = message[message.index("0x") : -1]
                    data["error"] = "revert"
                    data["reason"] = message
                else:
                    data["error"] = message
        return result
