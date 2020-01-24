#!/usr/bin/python3

from inspect import getmembers
from types import FunctionType

from hypothesis import settings
from hypothesis import stateful as sf
from hypothesis.strategies import SearchStrategy

import brownie


class _BrownieStateMachine:
    def __init__(self):
        brownie.rpc.revert()
        sf.RuleBasedStateMachine.__init__(self)


def _member_filter(member):
    attr, fn = member
    return (
        type(fn) is FunctionType
        and not hasattr(sf.RuleBasedStateMachine, attr)
        and not next((i for i in fn.__dict__.keys() if i.startswith("hypothesis_stateful")), False)
    )


def _generate_state_machine(rules_object):

    bases = (_BrownieStateMachine, rules_object, sf.RuleBasedStateMachine)
    machine = type("BrownieStateMachine", bases, {})
    strategies = {k: v for k, v in getmembers(rules_object) if isinstance(v, SearchStrategy)}

    for attr, fn in filter(_member_filter, getmembers(machine)):
        varnames = fn.__code__.co_varnames[1 : fn.__code__.co_argcount]
        if attr.startswith("initialize_"):
            wrapped = sf.initialize(**{key: strategies[key] for key in varnames})
            setattr(machine, attr, wrapped(fn))
        elif attr.startswith("invariant_"):
            setattr(machine, attr, sf.invariant()(fn))
        elif attr.startswith("rule_"):
            wrapped = sf.rule(**{key: strategies[key] for key in varnames})
            setattr(machine, attr, wrapped(fn))

    return machine


def state_machine(rules_object, *args, **kwargs):

    settings_dict = {"deadline": None}
    settings_dict.update(kwargs.pop("settings", {}))

    machine = _generate_state_machine(rules_object)
    if hasattr(rules_object, "__init__"):
        # __init__ is applied to the object, not the instance
        rules_object.__init__(machine, *args, **kwargs)
    brownie.rpc.snapshot()

    sf.run_state_machine_as_test(lambda: machine(), settings(**settings_dict))
