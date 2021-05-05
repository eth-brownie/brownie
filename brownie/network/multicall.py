from contextlib import contextmanager
from dataclasses import dataclass
from functools import partial
from types import FunctionType
from typing import List

from wrapt import ObjectProxy

from brownie import Contract


@dataclass
class Call:
    call: List
    decode_output: FunctionType


class Caller:
    def __init__(self, queue, contract=None, func=None):
        self.queue = queue
        self.contract = contract
        self.func = func

    def __getattr__(self, name):
        return Caller(self.queue, self.contract, getattr(self.contract, name))

    def __call__(self, *args, **kwds):
        future = Result(
            Call(
                [str(self.contract), self.func.encode_input(*args, **kwds)],
                self.func.decode_output,
            )
        )
        self.queue.append(future)
        return future


class Result(ObjectProxy):
    def __repr__(self):
        return repr(self.__wrapped__)


@contextmanager
def multicall_context(block_identifier=None):
    """
    with multicall_context() as caller:
        response = caller(contract).func(args)
    """
    queue = []
    yield partial(Caller, queue)

    multicall = Contract("0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696")
    results = multicall.tryAggregate.call(
        False, [request.call for request in queue], block_identifier=block_identifier
    )

    for request, (success, output) in zip(queue, results):
        request.__init__(request.decode_output(output) if success else None)
