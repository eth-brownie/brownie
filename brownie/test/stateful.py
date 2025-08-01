#!/usr/bin/python3

import sys
from inspect import getmembers
from types import FunctionType
from typing import Any, ClassVar, Dict, Final, Optional, final

from hypothesis import settings as hp_settings
from hypothesis import stateful as sf
from hypothesis.strategies import SearchStrategy
from mypy_extensions import mypyc_attr

import brownie
from brownie._c_constants import deque
from brownie.utils import red, yellow

sf.__tracebackhide__ = True  # type: ignore [attr-defined]

marker: Final = deque("-/|\\-/|\\")


@final
@mypyc_attr(native_class=False)
class _BrownieStateMachine:

    _failed: ClassVar[bool] = False
    _capman: ClassVar[Any] = None

    def __init__(self) -> None:
        brownie.chain.revert()
        sf.RuleBasedStateMachine.__init__(self)  # type: ignore [arg-type]

        # pytest capturemanager plugin, added when accessed via the state_manager fixture
        if capman := self._capman:
            with capman.global_and_fixture_disabled():
                color = red if self._failed else yellow
                sys.stdout.write(f"{color}{marker[0]}\033[1D")
                sys.stdout.flush()
            marker.rotate(1)

        if hasattr(self, "setup"):
            self.setup()  # type: ignore

    def execute_step(self, step) -> None:
        try:
            super().execute_step(step)  # type: ignore [misc]
        except Exception:
            type(self)._failed = True
            raise

    def check_invariants(self, settings) -> None:
        try:
            super().check_invariants(settings)  # type: ignore [misc]
        except Exception:
            type(self)._failed = True
            raise


def _member_filter(member: tuple[str, Any]) -> bool:
    attr, fn = member
    return (
        type(fn) is FunctionType
        and not hasattr(sf.RuleBasedStateMachine, attr)
        and not next((i for i in fn.__dict__.keys() if i.startswith("hypothesis_stateful")), False)
    )


def _attr_filter(attr: str, pattern: str) -> bool:
    return attr == pattern or attr.startswith(f"{pattern}_")


def _generate_state_machine(rules_object: type) -> type:

    bases = (_BrownieStateMachine, rules_object, sf.RuleBasedStateMachine)
    machine = type("BrownieStateMachine", bases, {})
    strategies: Dict[str, SearchStrategy] = {k: v for k, v in getmembers(rules_object) if isinstance(v, SearchStrategy)}

    for member in getmembers(machine):
        if _member_filter(member):
            attr, fn = member
            varnames = [[i] for i in fn.__code__.co_varnames[1 : fn.__code__.co_argcount]]
            if fn.__defaults__:
                for i in range(-1, -1 - len(fn.__defaults__), -1):
                    varnames[i].append(fn.__defaults__[i])
    
            if _attr_filter(attr, "initialize"):
                wrapped = sf.initialize(**{key[0]: strategies[key[-1]] for key in varnames})  # type: ignore [call-overload]
                setattr(machine, attr, wrapped(fn))
            elif _attr_filter(attr, "invariant"):
                setattr(machine, attr, sf.invariant()(fn))
            elif _attr_filter(attr, "rule"):
                wrapped = sf.rule(**{key[0]: strategies[key[-1]] for key in varnames})  # type: ignore [call-overload]
                setattr(machine, attr, wrapped(fn))

    return machine


def state_machine(
    rules_object: type, *args: Any, settings: Optional[dict] = None, **kwargs: Any
) -> None:

    machine = _generate_state_machine(rules_object)
    if hasattr(rules_object, "__init__"):
        # __init__ is treated as a class method
        rules_object.__init__(machine, *args, **kwargs)  # type: ignore
    brownie.chain.snapshot()

    try:
        sf.run_state_machine_as_test(lambda: machine(), settings=hp_settings(**settings or {}))
    finally:
        if hasattr(machine, "teardown_final"):
            # teardown_final is also a class method
            machine.teardown_final(machine)  # type: ignore
