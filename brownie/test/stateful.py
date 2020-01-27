#!/usr/bin/python3

from inspect import getmembers
from types import FunctionType
from typing import Any, Optional

from hypothesis import settings as hp_settings
from hypothesis import stateful as sf
from hypothesis.strategies import SearchStrategy

import brownie

__tracebackhide__ = True
sf.__tracebackhide__ = True


class _BrownieStateMachine:
    def __init__(self) -> None:
        brownie.rpc.revert()
        sf.RuleBasedStateMachine.__init__(self)
        if hasattr(self, "setup"):
            self.setup()  # type: ignore


def _member_filter(member: tuple) -> bool:
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
    strategies = {k: v for k, v in getmembers(rules_object) if isinstance(v, SearchStrategy)}

    for attr, fn in filter(_member_filter, getmembers(machine)):
        varnames = fn.__code__.co_varnames[1 : fn.__code__.co_argcount]
        if _attr_filter(attr, "initialize"):
            wrapped = sf.initialize(**{key: strategies[key] for key in varnames})
            setattr(machine, attr, wrapped(fn))
        elif _attr_filter(attr, "invariant"):
            setattr(machine, attr, sf.invariant()(fn))
        elif _attr_filter(attr, "rule"):
            wrapped = sf.rule(**{key: strategies[key] for key in varnames})
            setattr(machine, attr, wrapped(fn))

    return machine


def state_machine(
    rules_object: type, *args: Any, settings: Optional[dict] = None, **kwargs: Any
) -> None:

    machine = _generate_state_machine(rules_object)
    if hasattr(rules_object, "__init__"):
        # __init__ is treated as a class method
        rules_object.__init__(machine, *args, **kwargs)  # type: ignore
    brownie.rpc.snapshot()

    try:
        sf.run_state_machine_as_test(lambda: machine(), hp_settings(**settings or {}))
    finally:
        if hasattr(machine, "teardown_final"):
            # teardown_final is also a class method
            machine.teardown_final(machine)  # type: ignore
