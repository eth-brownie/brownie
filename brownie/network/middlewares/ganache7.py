from typing import Any, TypedDict, cast, final

from typing_extensions import NotRequired
from web3 import Web3
from web3.exceptions import Web3RPCError
from web3.types import MakeRequestFn, RPCEndpoint, RPCResponse

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


class GanacheVmErrorData(TypedDict, total=False):
    hash: str
    message: str
    programCounter: int | None
    result: str
    reason: str | None


class _GanacheRPCError(TypedDict):
    message: str
    data: NotRequired[str | GanacheVmErrorData | dict[str, LegacyGanacheErrorData]]


def _normalize_transaction_error(error: _GanacheRPCError) -> None:
    provider_data = cast(GanacheVmErrorData, error["data"])
    tx_data: LegacyGanacheErrorData = {
        "error": provider_data["message"],
        "program_counter": provider_data["programCounter"],
    }
    if "result" in provider_data:
        tx_data["result"] = provider_data["result"]
    if "reason" in provider_data:
        tx_data["reason"] = provider_data["reason"]
    normalized_data: dict[str, LegacyGanacheErrorData] = {}
    normalized_data[provider_data["hash"]] = tx_data
    error["data"] = normalized_data


def _normalize_call_error(error: _GanacheRPCError) -> None:
    if error.get("message", "").startswith("VM Exception"):
        # "VM Exception while processing transaction: {reason} {message}"
        msg: str = error["message"]
        msg = msg.split(": ", maxsplit=1)[-1]
        if msg.startswith("revert"):
            call_data: LegacyGanacheErrorData = {
                "error": "revert",
                "reason": cast(str, error["data"]),
            }
        else:
            call_data = {"error": msg, "reason": None}
        error["data"] = {"0x": call_data}


@final
class Ganache7MiddleWare(BrownieMiddlewareABC):
    @classmethod
    def get_layer(cls, w3: Web3, network_type: str) -> int | None:
        return -100 if w3.client_version.lower().startswith("ganache/v7") else None

    def process_request(
        self,
        make_request: MakeRequestFn,
        method: RPCEndpoint,
        params: Any,
    ) -> RPCResponse:
        try:
            result = make_request(method, params)
        except Web3RPCError as exc:
            err_response = exc.rpc_response
            if err_response is None:
                raise
            result = err_response

        # reformat failed eth_call / eth_sendTransaction output to mimic that of Ganache 6.x
        # yes, this is hacky and awful and in the future we should stop supporting
        # the older version of ganache. but doing so will cause unexpected issues
        # in projects that are still pinned to the old version, so for now we support
        # both and simply raise a warning of a pending deprecation.
        if (
            method in {"eth_sendTransaction", "eth_sendRawTransaction"}
            and "error" in result
            and "data" in (error := cast(_GanacheRPCError, result["error"]))
        ):
            _normalize_transaction_error(error)

        if method == "eth_call" and "error" in result:
            error = cast(_GanacheRPCError, result["error"])
            _normalize_call_error(error)

        return result
