#!/usr/bin/python3

import pytest

from brownie.test import state_machine


def test_teardown_called_on_each_run(SMTestBase):
    class StateMachine(SMTestBase):
        setup_count = 0
        teardown_count = 0

        def setup(self):
            type(self).setup_count += 1
            assert self.teardown_count == self.setup_count - 1

        def teardown(self):
            type(self).teardown_count += 1

    state_machine(StateMachine, settings={"max_examples": 5})


def test_teardown_final_called(SMTestBase):
    class StateMachine(SMTestBase):
        def teardown_final(self):
            raise AssertionError("I am a potato")

    with pytest.raises(AssertionError, match="I am a potato"):
        state_machine(StateMachine, settings={"max_examples": 5})


def test_teardown_final_called_on_failed_test(SMTestBase):
    class StateMachine(SMTestBase):
        def rule_one(self):
            assert False

        def teardown_final(self):
            raise AssertionError("I am a potato")

    with pytest.raises(AssertionError, match="I am a potato"):
        state_machine(StateMachine, settings={"max_examples": 5})


def test_teardown_final_only_called_once(SMTestBase):
    class StateMachine(SMTestBase):
        def teardown_final(self):
            assert not hasattr(self, "foo")
            self.foo = "foo"

    state_machine(StateMachine, settings={"max_examples": 5})
