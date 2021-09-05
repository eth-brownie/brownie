import json
from collections import defaultdict
from dataclasses import dataclass
from threading import Lock, get_ident
from types import FunctionType, TracebackType
from typing import Any, Dict, List, Optional, Tuple, Union

from lazy_object_proxy import Proxy
from wrapt import ObjectProxy

from brownie._config import BROWNIE_FOLDER, CONFIG
from brownie.exceptions import ContractNotFound
from brownie.network import accounts, web3
from brownie.network.contract import Contract, ContractCall
from brownie.project import compile_source

DATA_DIR = BROWNIE_FOLDER.joinpath("data")
MULTICALL2_ABI = json.loads(DATA_DIR.joinpath("interfaces", "Multicall2.json").read_text())
MULTICALL2_SOURCE = DATA_DIR.joinpath("contracts", "Multicall2.sol").read_text()


@dataclass
class Call:

    calldata: Tuple[str, bytes]
    decoder: FunctionType


class Result(ObjectProxy):
    """A proxy object to be updated with the result of a multicall."""

    def __repr__(self) -> str:
        return repr(self.__wrapped__)


class LazyResult(Proxy):
    """A proxy object to be updated with the result of a multicall."""

    def __repr__(self) -> str:
        return repr(self.__wrapped__)


class Multicall:
    """Context manager for batching multiple calls to constant contract functions."""

    _lock = Lock()

    def __init__(self) -> None:
        self.address = None
        self._block_number = defaultdict(lambda: None)  # type: ignore
        self._contract = None
        self._pending_calls: Dict[int, List[Call]] = defaultdict(list)

        setattr(ContractCall, "__original_call_code", ContractCall.__call__.__code__)
        setattr(ContractCall, "__proxy_call_code", self._proxy_call.__code__)
        setattr(ContractCall, "__multicall", defaultdict(lambda: None))
        ContractCall.__call__.__code__ = self._proxy_call.__code__

    @property
    def block_number(self) -> int:
        return self._block_number[get_ident()]

    def __call__(
        self, address: Optional[str] = None, block_identifier: Union[str, bytes, int, None] = None
    ) -> "Multicall":
        self.address = address  # type: ignore
        self._block_number[get_ident()] = block_identifier  # type: ignore
        return self

    def _flush(self, future_result: Result = None) -> Any:
        pending_calls = self._pending_calls[get_ident()]
        self._pending_calls[get_ident()] = []

        if not pending_calls:
            # either all calls have already been made
            # or this result has already been retrieved
            return future_result
        with self._lock:
            ContractCall.__call__.__code__ = getattr(ContractCall, "__original_call_code")
            results = self._contract.tryAggregate(  # type: ignore
                False,
                [_call.calldata for _call in pending_calls],
                block_identifier=self._block_number[get_ident()],
            )
            ContractCall.__call__.__code__ = getattr(ContractCall, "__proxy_call_code")

        for _call, result in zip(pending_calls, results):
            _call.__wrapped__ = _call.decoder(result[1]) if result[0] else None  # type: ignore

        return future_result

    def flush(self) -> Any:
        """Flush the pending queue of calls, retrieving all the results."""
        return self._flush()

    def _call_contract(self, call: ContractCall, *args: Tuple, **kwargs: Dict[str, Any]) -> Proxy:
        """Add a call to the buffer of calls to be made"""
        calldata = (call._address, call.encode_input(*args, **kwargs))  # type: ignore
        call_obj = Call(calldata, call.decode_output)  # type: ignore
        # future result
        result = Result(call_obj)
        self._pending_calls[get_ident()].append(result)

        return LazyResult(lambda: self._flush(result))

    @staticmethod
    def _proxy_call(*args: Tuple, **kwargs: Dict[str, Any]) -> Any:
        """Proxy code which substitutes `ContractCall.__call__"""
        self = getattr(ContractCall, "__multicall", {}).get(get_ident())
        if self:
            return self._call_contract(*args, **kwargs)

        # standard call we let pass through
        ContractCall.__call__.__code__ = getattr(ContractCall, "__original_call_code")
        result = ContractCall.__call__(*args, **kwargs)  # type: ignore
        ContractCall.__call__.__code__ = getattr(ContractCall, "__proxy_call_code")
        return result

    def __enter__(self) -> "Multicall":
        """Enter the Context Manager and substitute `ContractCall.__call__`"""
        # we set the code objects on ContractCall class so we can grab them later

        active_network = CONFIG.active_network

        if "multicall2" in active_network:
            self.address = active_network["multicall2"]
        elif "cmd" in active_network:
            deployment = self.deploy({"from": accounts[0]})
            self.address = deployment.address  # type: ignore
            self._block_number[get_ident()] = deployment.tx.block_number  # type: ignore

        self._block_number[get_ident()] = (
            self._block_number[get_ident()] or web3.eth.get_block_number()
        )

        if self.address is None:
            raise ContractNotFound(
                "Must set Multicall address via `brownie.multicall(address=...)`"
            )
        elif not web3.eth.get_code(self.address, block_identifier=self.block_number):
            raise ContractNotFound(
                f"Multicall at address {self.address} does not exist at block {self.block_number}"
            )

        self._contract = Contract.from_abi("Multicall", self.address, MULTICALL2_ABI)
        getattr(ContractCall, "__multicall")[get_ident()] = self

    def __exit__(self, exc_type: Exception, exc_val: Any, exc_tb: TracebackType) -> None:
        """Exit the Context Manager and reattach original `ContractCall.__call__` code"""
        self.flush()
        getattr(ContractCall, "__multicall")[get_ident()] = None

    @staticmethod
    def deploy(tx_params: Dict) -> Contract:
        """Deploy an instance of the `Multicall2` contract.

        Args:
            tx_params: parameters passed to the `deploy` method of the `Multicall2` contract
                container.
        """
        project = compile_source(MULTICALL2_SOURCE)
        deployment = project.Multicall2.deploy(tx_params)  # type: ignore
        CONFIG.active_network["multicall2"] = deployment.address
        return deployment
