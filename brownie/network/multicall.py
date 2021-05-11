import json
from contextlib import contextmanager
from dataclasses import dataclass
from functools import partial
from types import FunctionType
from typing import Dict, Iterator, List, Tuple, Union

from wrapt import ObjectProxy

from brownie import Contract
from brownie._config import BROWNIE_FOLDER

with (BROWNIE_FOLDER / "data/interfaces/Multicall2.json").open() as f:
    MULTICALL2_ABI = json.load(f)


@dataclass
class Call:
    """Dataclass representing a call to be made via Multicall2.

    Attributes:
        call: A tuple composed of the target address and the bytes calldata to be sent.
        decode_output: A function to decode the bytes returndata after a successful call.
    """

    call: Tuple[str, bytes]
    decode_output: FunctionType


class Result(ObjectProxy):
    """A proxy object to be updated with the result of a multicall."""

    def __repr__(self) -> str:
        return repr(self.__wrapped__)


class Caller:
    """Contract call catcher, which maintains a list of all calls to be made via multicall2.

    Attributes:
        queue: A list of result proxy objects to be updated after the call to multicall2.
        contract: The contract instance which calls are being made through.
        func: The contract function which calls are being made to. This funciton will have
            `encode_input` and `decode_output` methods available.
    """

    def __init__(
        self, queue: List[Result], contract: Contract = None, func: FunctionType = None
    ) -> None:
        self.queue = queue
        self.contract = contract
        self.func = func

    def __getattr__(self, name: str) -> "Caller":
        """Returns a Caller object which wraps around a contract method."""
        return Caller(self.queue, self.contract, getattr(self.contract, name))

    def __call__(self, *args: Tuple, **kwargs: Dict) -> Result:
        """Returns a proxy object which is updated when the multicall ctxmanager exits."""
        future = Result(
            Call(
                (self.contract.address, self.func.encode_input(*args, **kwargs)),  # type: ignore
                self.func.decode_output,  # type: ignore
            )
        )
        self.queue.append(future)
        return future


@contextmanager
def multicall(
    address: str, block_identifier: Union[int, bytes, str] = None
) -> Iterator[partial(Caller)]:  # type: ignore
    """Multicall2 context manager for atomic reads.

    Multicall allows for atomic reads from a specific block, and a significantly reduced
    number of RPC calls.

    Args:
        address: The address of the Multicall2 contract.
        block_identifier: A block number or hash that the call is executed at. If not given, the
            latest block used.

    Examples:
        A rather long but simple example:

        >>> from brownie import multicall, ERC20
        >>> import pandas as pd
        >>> tokens = ("0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e",)
        >>> with multicall("0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696") as call:
        ...     records = []
        ...     for addr in tokens:
        ...         token = ERC20.at(addr)
        ...         name = call(token).name()
        ...         symbol = call(token).symbol()
        ...         total_supply = call(token).totalSupply()
        ...         records.append([token.address, name, symbol, total_supply])
        ... df = pd.DataFrame.from_records(records, columns=["addr", "name", "symb", "totalSupply"])
        ... print(df)
                                                addr           name    symb              totalSupply
        0  0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e  yearn.finance    YFI  36666000000000000000000
        ...
    """
    queue: List[Result] = []
    yield partial(Caller, queue)

    multicall2 = Contract.from_abi("Multicall2", address, MULTICALL2_ABI)
    results = multicall2.tryAggregate.call(
        False, [request.call for request in queue], block_identifier=block_identifier
    )

    for request, (success, output) in zip(queue, results):
        request.__wrapped__ = request.decode_output(output) if success else None
