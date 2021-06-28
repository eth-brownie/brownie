import json
from dataclasses import dataclass
from types import FunctionType, TracebackType
from typing import Any, Dict, List, Tuple, Union

from lazy_object_proxy import Proxy
from wrapt import ObjectProxy

from brownie import accounts, chain, web3
from brownie._config import BROWNIE_FOLDER, CONFIG
from brownie.exceptions import ContractNotFound
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
    def __init__(
        self, address: str = None, block_identifier: Union[int, str, bytes] = None
    ) -> None:
        self.address = address
        self.block_identifier = block_identifier or chain.height
        self._pending_calls: List[Call] = []
        self._complete = True

        if address is None:
            active_network = CONFIG.active_network

            if "multicall2" in active_network:
                self.address = active_network["multicall2"]
            elif "cmd" in active_network:
                if block_identifier is not None:
                    raise ContractNotFound(
                        f"Must deploy Multicall2 before block {self.block_identifier}. "
                        "Use `Multicall2.deploy` classmethod to deploy an instance of Multicall2."
                    )
                deployment = self.deploy({"from": accounts[0]})
                self.address = deployment.address
                self.block_identifier = deployment.tx.block_number  # type: ignore
            else:
                # live network and no address
                raise ContractNotFound("Must provide Multicall2 address as argument")

        if not web3.eth.get_code(self.address, self.block_identifier):
            # TODO: Handle deploying multicall in a test network without breaking the expected chain
            # For Geth client's we can use state override to have multicall at any arbitrary address
            raise ContractNotFound(
                f"Multicall2 at `{self.address}` not available at block `{self.block_identifier}`"
            )

        contract = Contract.from_abi("Multicall2", self.address, MULTICALL2_ABI)  # type: ignore
        self._contract = contract

    def _flush(self, future_result: Result = None) -> Any:
        if not self._pending_calls:
            # either all calls have already been made
            # or this result has already been retrieved
            return future_result
        ContractCall.__call__.__code__ = getattr(ContractCall, "__original_call_code")
        results = self._contract.tryAggregate(
            False,
            [_call.calldata for _call in self._pending_calls],
            block_identifier=self.block_identifier,
        )
        if not self._complete:
            ContractCall.__call__.__code__ = getattr(ContractCall, "__proxy_call_code")
        for _call, result in zip(self._pending_calls, results):
            _call.__wrapped__ = _call.decoder(result[1]) if result[0] else None  # type: ignore
        self._pending_calls = []  # empty the pending calls
        return future_result

    def flush(self) -> Any:
        return self._flush()

    def _call_contract(self, call: ContractCall, *args: Tuple, **kwargs: Dict[str, Any]) -> Proxy:
        """Add a call to the buffer of calls to be made"""
        calldata = (call._address, call.encode_input(*args, **kwargs))  # type: ignore
        call_obj = Call(calldata, call.decode_output)  # type: ignore
        # future result
        result = Result(call_obj)
        self._pending_calls.append(result)

        return LazyResult(lambda: self._flush(result))

    @staticmethod
    def _proxy_call(*args: Tuple, **kwargs: Dict[str, Any]) -> Any:
        """Proxy code which substitutes `ContractCall.__call__`

        This makes constant contract calls look more like transactions since we require
        users to specify a dictionary as the last argument with the from field
        being the multicall2 instance being used."""
        if args and isinstance(args[-1], dict):
            args, tx = args[:-1], args[-1]
            self = tx["from"]
            return self._call_contract(*args, **kwargs)

        # standard call we let pass through
        ContractCall.__call__.__code__ = getattr(ContractCall, "__original_call_code")
        result = ContractCall.__call__(*args, **kwargs)  # type: ignore
        ContractCall.__call__.__code__ = getattr(ContractCall, "__proxy_call_code")
        return result

    def __enter__(self) -> "Multicall":
        """Enter the Context Manager and substitute `ContractCall.__call__`"""
        # we set the code objects on ContractCall class so we can grab them later
        if not hasattr(ContractCall, "__original_call_code"):
            setattr(ContractCall, "__original_call_code", ContractCall.__call__.__code__)
            setattr(ContractCall, "__proxy_call_code", self._proxy_call.__code__)
        ContractCall.__call__.__code__ = self._proxy_call.__code__
        self.flush()
        self._complete = False
        return self

    def __exit__(self, exc_type: Exception, exc_val: Any, exc_tb: TracebackType) -> None:
        """Exit the Context Manager and reattach original `ContractCall.__call__` code"""
        self.flush()
        self._complete = True
        ContractCall.__call__.__code__ = getattr(ContractCall, "__original_call_code")

    @classmethod
    def deploy(cls, tx_params: Dict) -> Contract:
        project = compile_source(MULTICALL2_SOURCE)
        deployment = project.Multicall2.deploy(tx_params)  # type: ignore
        CONFIG.active_network["multicall2"] = deployment.address
        return deployment