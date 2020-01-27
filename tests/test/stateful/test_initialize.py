#!/usr/bin/python3

import pytest
from hypothesis import stateful as sf

from brownie.test import state_machine, strategy


def test_initializes_run(SMTestBase):
    class StateMachine(SMTestBase):
        def __init__(self, value):
            self.value = value

        def initialize_one(self):
            assert self.value

        def initialize_two(self):
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

        def initialize_one(self, st_int):
            assert type(st_int) is int
            assert 0 <= st_int <= 255

        def initialize_two(self, st_bool, foobar):
            assert type(st_bool) is bool
            assert type(foobar) is bytes

        def initialize_three(self, boo="foobar"):
            assert type(boo) is bytes

    state_machine(StateMachine, settings={"max_examples": 5})


def test_decoration(SMTestBase):
    class StateMachine(SMTestBase):
        initialize_trap = "potato"
        initialize_othertrap = strategy("bool")

    state_machine(StateMachine, settings={"max_examples": 5})


def test_existing_decorators(SMTestBase):
    class StateMachine(SMTestBase):
        @sf.initialize(st_int=strategy("uint8"))
        def initialize_one(self, st_int):
            pass

        @sf.initialize()
        def rule_horrible_name_for_intializer(self):
            pass

    state_machine(StateMachine, settings={"max_examples": 5})


def test_single_initialize(SMTestBase):
    class StateMachine(SMTestBase):
        def initialize(self):
            assert False

    with pytest.raises(AssertionError):
        state_machine(StateMachine, settings={"max_examples": 5})
