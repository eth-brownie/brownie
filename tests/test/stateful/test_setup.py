#!/usr/bin/python3

from hypothesis.stateful import StateMachineMeta

from brownie.test import state_machine


def test_base_class_isolated(SMTestBase):
    # changes to class attributes while running a state machine
    # should not affect the original class
    class StateMachine(SMTestBase):
        value = 42

        def __init__(self):
            self.value = 31337

        def rule_one(self):
            type(self).value = 31337

        def rule_two(self):
            type(self).value = 31337

        def teardown(self):
            assert type(self).value == 31337

    assert StateMachine.value == 42
    state_machine(StateMachine, settings={"max_examples": 5})
    assert StateMachine.value == 42


def test_init_only_called_once(SMTestBase):
    class StateMachine(SMTestBase):
        count = 0

        def __init__(self):
            assert not self.count
            self.count += 1

    state_machine(StateMachine, settings={"max_examples": 5})


def test_without_init(SMTestBase):

    state_machine(SMTestBase, settings={"max_examples": 2})


def test_init_runs_on_class(SMTestBase):
    class StateMachine(SMTestBase):
        def __init__(self):
            assert type(self) is StateMachineMeta

    state_machine(StateMachine, settings={"max_examples": 2})


def test_init_receives_args_and_kwargs(SMTestBase):
    class StateMachine(SMTestBase):
        def __init__(self, foo, bar=42, baz=31337):
            assert foo == 11
            assert bar in (32, 42)
            assert baz in (69, 31337)

    state_machine(StateMachine, 11, baz=69, settings={"max_examples": 2})


def test_rpc_reverts_between_runs(SMTestBase, accounts, web3):
    class StateMachine(SMTestBase):
        def initialize_one(self):
            assert web3.eth.block_number == 1
            accounts[0].transfer(accounts[1], 100)

    accounts[0].transfer(accounts[1], 100)
    state_machine(StateMachine, settings={"max_examples": 5})


def test_misc_methods(SMTestBase):
    class StateMachine(SMTestBase):
        def foo(self):
            pass

        def bar(self):
            pass

    state_machine(StateMachine, settings={"max_examples": 5})


def test_setup_called_on_each_run(SMTestBase):
    class StateMachine(SMTestBase):
        foo = "foo"

        def setup(self):
            assert self.foo == "foo"
            self.foo = "bar"

        def teardown(self):
            assert self.foo == "bar"

    state_machine(StateMachine, settings={"max_examples": 5})
