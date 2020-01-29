#!/usr/bin/python3

import pytest
from hypothesis import stateful as sf

from brownie.test import state_machine, strategy


def test_invariants_run(SMTestBase):
    class StateMachine(SMTestBase):
        def __init__(self, value):
            self.value = value

        def invariant_one(self):
            assert self.value

        def invariant_two(self):
            assert not self.value

    with pytest.raises(AssertionError):
        state_machine(StateMachine, True, settings={"max_examples": 5})

    with pytest.raises(AssertionError):
        state_machine(StateMachine, False, settings={"max_examples": 5})


def test_invariants_always_run(SMTestBase):
    class StateMachine(SMTestBase):
        def __init__(self):
            self.counts = [0, 0]

    def invariant_one(self):
        self.counts[0] += 1

    def invariant_two(self):
        self.counts[1] += 1

    def teardown(self):
        assert self.counts[0] > 0
        assert self.counts[0] == self.counts[1]

    state_machine(StateMachine, settings={"max_examples": 5})


def test_strategy_injection_fails(SMTestBase):
    class StateMachine(SMTestBase):
        st_int = strategy("uint8")

        def invariant_one(self, st_int):
            pass

    with pytest.raises(TypeError):
        state_machine(StateMachine, settings={"max_examples": 5})


def test_decoration(SMTestBase):
    class StateMachine(SMTestBase):
        invariant_trap = "potato"
        invariant_othertrap = strategy("bool")

    state_machine(StateMachine, settings={"max_examples": 5})


def test_existing_decorators(SMTestBase):
    class StateMachine(SMTestBase):
        @sf.invariant()
        def invariant_one(self):
            pass

        @sf.invariant()
        def initialize_horrible_name_for_invariant(self):
            pass

    state_machine(StateMachine, settings={"max_examples": 5})


def test_single_invariant(SMTestBase):
    class StateMachine(SMTestBase):
        foo = "foo"

    def invariant(self):
        self.foo = "bar"

    def teardown(self):
        assert self.foo == "bar"

    state_machine(StateMachine, settings={"max_examples": 5})
