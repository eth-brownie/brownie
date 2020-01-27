#!/usr/bin/python3

import pytest
from hypothesis import stateful as sf

from brownie.test import state_machine, strategy


def test_rules_run(SMTestBase):
    class StateMachine(SMTestBase):
        def __init__(self, value):
            self.value = value

        def rule_one(self):
            assert self.value

        def rule_two(self):
            assert not self.value

    with pytest.raises(AssertionError):
        state_machine(StateMachine, True, settings={"max_examples": 5})

    with pytest.raises(AssertionError):
        state_machine(StateMachine, False, settings={"max_examples": 5})


def test_strategy_injection(SMTestBase):
    class StateMachine(SMTestBase):
        st_int = strategy("uint8")
        st_bool = strategy("bool")
        foobar = strategy("bytes4")

        def rule_one(self, st_int):
            assert type(st_int) is int
            assert 0 <= st_int <= 255

        def rule_two(self, st_bool, foobar):
            assert type(st_bool) is bool
            assert type(foobar) is bytes

        def rule_three(self, foo="st_bool"):
            assert type(foo) is bool

    state_machine(StateMachine, settings={"max_examples": 5})


def test_decoration(SMTestBase):
    class StateMachine(SMTestBase):
        rule_trap = "potato"
        rule_othertrap = strategy("bool")

    state_machine(StateMachine, settings={"max_examples": 5})


def test_existing_decorators(SMTestBase):
    class StateMachine(SMTestBase):
        @sf.rule(st_int=strategy("uint8"))
        def rule_one(self, st_int):
            pass

        @sf.rule()
        def invariant_horrible_name_for_a_rule(self):
            pass

    state_machine(StateMachine, settings={"max_examples": 5})


def test_single_rule(SMTestBase):
    class StateMachine(SMTestBase):
        def rule(self):
            assert False

    with pytest.raises(AssertionError):
        state_machine(StateMachine, settings={"max_examples": 5})
