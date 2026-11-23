.. _hypothesis-stateful:

================
Stateful Testing
================

`Stateful testing` is a more advanced method of :ref:`property-based testing<hypothesis>` used to test complex systems. In a stateful test you define a number of actions that can be combined together in different ways, and Hypothesis attempts to find a sequence of those actions that result in a failure. This is useful for testing complex contracts or contract-to-contract interactions where there are many possible states.

Brownie utilizes the ``hypothesis`` framework to allow for stateful testing.

Much of the content in this section is based on the official `hypothesis.works <https://hypothesis.works/>`_ website. To learn more about stateful testing, you may wish to read the following articles:

* `Rule Based Stateful Testing <https://hypothesis.works/articles/rule-based-stateful-testing/>`_ by David R. MacIver
* `Solving the Water Jug Problem from Die Hard 3 with TLA+ and Hypothesis <https://hypothesis.works/articles/how-not-to-die-hard-with-hypothesis/>`_ by Nicholas Chammas
* `Hypothesis Documentation <https://hypothesis.readthedocs.io/en/latest/stateful.html>`_ on stateful testing

.. warning::

    This functionality is still under development and should be considered experimental. Use common sense when evaluating the results, and if you encounter any problems please `open an issue <https://github.com/eth-brownie/brownie/issues>`_ on Github.


Rule-based State Machines
=========================

A state machine is a class used within stateful testing. It defines the initial test state, a number of actions outlining the structure that the test will execute in, and invariants that should not be violated during execution.

.. note::

    Unlike regular Hypothesis state machines, Brownie state machines should not subclass :py:class:`RuleBasedStateMachine <hypothesis.stateful.RuleBasedStateMachine>`.

Rules
-----

At the core of every state machine are one or more `rules`.  Rules are class methods that are very similar to ``@given`` based tests; they receive values drawn from strategies and pass them to a user defined test function. The key difference is that where ``@given`` based tests run independently, rules can be chained together - a single stateful test run may involve multiple rule invocations, which may interact in various ways.

Any state machine method named ``rule`` or beginning with ``rule_`` is treated as a rule.

.. code-block:: python

    class StateMachine:

        def rule_one(self):
            # performs a test action

        def rule_two(self):
            # performs another, different test action

Initializers
------------

There is also a special type of rule known as an `initializer`. These are rules that are guaranteed to be executed at most one time at the beginning of a run (i.e. before any normal rule is called). They may be called in any order, or not at all, and the order will vary from run to run.

Any state machine method named ``initialize`` or beginning with ``initialize_`` is treated as an initializer.

.. code-block:: python

    class StateMachine:

        def initialize(self):
            # this method may or may not be called prior to rule_two

        def rule(self):
            # once this method is called, initialize will not be called during the test run

Strategies
----------

A state machine should contain one or more :ref:`strategies <hypothesis-strategies>`, in order to provide data to it's rules.

Strategies must be defined at the class level, typically before the first function. They can be given any name.

Similar to how fixtures work within pytest tests, state machine rules receive strategies by referencing them within their arguments. This is shown in the following example:

.. code-block:: python

    class StateMachine:

        st_uint = strategy('uint256')
        st_bytes32 = strategy('bytes32')

        def initialize(self, st_uint):
            # this method draws from the uint256 strategy

        def rule(self, st_uint, st_bytes32):
            # this method draws from both strategies

        def rule_two(self, value="st_uint", othervalue="st_uint"):
            # this method draws from the same strategy twice

Invariants
----------

Along with rules, a state machine often defines `invariants`. These are properties that should remain unchanged, regardless of any actions performed by the rules. After each rule is executed, every invariant method is always called to ensure that the test has not failed.

Any state machine method named ``invariant`` or beginning with ``invariant_`` is treated as an invariant. Invariants are meant for verifying correctness of state; they cannot receive strategies.

.. code-block:: python

    class StateMachine:

        def rule_one(self):
            pass

        def rule_two(self):
            pass

        def invariant(self):
            # assertions in this method should always pass regardless
            # of actions in both rule_one and rule_two

Setup and Teardown
------------------

A state machine may optionally include setup and teardown procedures. Similar to pytest fixtures, setup and teardown methods are available to execute logic on a per-test and per-run basis.

.. py:classmethod:: StateMachine.__init__(cls, *args)

    This method is called once, prior to the chain snapshot taken before the first test run. It is run as a class method - changes made to the state machine will persist through every run of the test.

    ``__init__`` is the only method that can be used to pass external data into the state machine. In the following example, we use it to pass the :ref:`accounts<test-fixtures-accounts>` fixture, and a deployed instance of a token contract:

    .. code-block:: python

        class StateMachine:

            def __init__(cls, accounts, token):
                cls.accounts = accounts
                cls.token = token


        def test_stateful(Token, accounts, state_machine):
            token = Token.deploy("Test Token", "TST", 18, 1e23, {'from': accounts[0]})

            # state_machine forwards all the arguments to StateMachine.__init__
            state_machine(StateMachine, accounts, token)

.. py:classmethod:: StateMachine.setup(self)

    This method is called at the beginning of each test run, immediately after chain is reverted to the snapshot. Changes applied during ``setup`` will only have an effect for the upcoming run.

.. py:classmethod:: StateMachine.teardown(self)

    This method is called at the end of each successful test run, prior to the chain revert. ``teardown`` is not called if the run fails.

.. py:classmethod:: StateMachine.teardown_final(cls)

    This method is called after the final test run has completed and the chain has been reverted. ``teardown_final`` is called regardless of whether the test passed or failed.

Test Execution Sequence
=======================

A Brownie stateful test executes in the following sequence:

    1. The setup phase of all pytest fixtures are executed in their regular order.
    2. If present, the ``StateMachine.__init__`` method is called.
    3. A snapshot of the current chain state is taken.
    4. If present, the ``StateMachine.setup`` method is called.
    5. Zero or more ``StateMachine`` initialize methods are called, in no particular order.
    6. One or more ``StateMachine`` rule methods are called, in no particular order.
    7. After each initialize and rule, every ``StateMachine`` invariant method is called.
    8. If present, the ``StateMachine.teardown`` method is called.
    9. The chain is reverted to the snapshot taken in step 3.
    10. Steps 4-9 are repeated 50 times, or until the test fails.
    11. If present, the ``StateMachine.teardown_final`` method is called.
    12. The teardown phase of all pytest fixtures are executed in their normal order.

Writing Stateful Tests
======================

To write a stateful test:

1. Create a state machine class.
2. Create a regular pytest-style test that includes the :func:`state_machine <fixtures.state_machine>` fixture.
3. Within the test, call :func:`state_machine <stateful.state_machine>` with the state machine as the first argument.

.. py:method:: brownie.test.stateful.state_machine(state_machine_class, *args, settings=None)

    Executes a stateful test.

    * ``state_machine_class``: A state machine class to be used in the test. Be sure to pass the class itself, not an instance of the class.
    * ``*args``: Any arguments given here will be passed to the state machine's ``__init__`` method.
    * ``settings``: An optional :py:class:`dict <dict>` of :ref:`Hypothesis settings<hypothesis-settings>` that will replace the defaults for this test only.

    This method is available as a pytest fixture :func:`state_machine <fixtures.state_machine>`.

Basic Example
-------------

As a basic example, we will create a state machine to test the following Vyper ``Depositer`` contract. This is very simple contract with two functions and a public mapping. Anyone can deposit ether for another account using the ``deposit_for`` method, or withdraw deposited ether using ``withdraw_from``.

.. code-block:: python
    :linenos:

    deposited: public(HashMap[address, uint256])

    @external
    @payable
    def deposit_for(_receiver: address) -> bool:
        self.deposited[_receiver] += msg.value
        return True

    @external
    def withdraw_from(_value: uint256) -> bool:
        assert self.deposited[msg.sender] >= _value, "Insufficient balance"
        self.deposited[msg.sender] = _value
        send(msg.sender, _value)
        return True

If you looked closely you may have noticed a major issue in the contract code. If not, don't worry! We're going to find it using our test.

Here is a state machine and test function we can use to test the contract.

.. code-block:: python

    import brownie
    from brownie.test import strategy

    class StateMachine:

        value = strategy('uint256', max_value="1 ether")
        address = strategy('address')

        def __init__(cls, accounts, Depositer):
            # deploy the contract at the start of the test
            cls.accounts = accounts
            cls.contract = Depositer.deploy({'from': accounts[0]})

        def setup(self):
            # zero the deposit amounts at the start of each test run
            self.deposits = {i: 0 for i in self.accounts}

        def rule_deposit(self, address, value):
            # make a deposit and adjust the local record
            self.contract.deposit_for(address, {'from': self.accounts[0], 'value': value})
            self.deposits[address] += value

        def rule_withdraw(self, address, value):
            if self.deposits[address] >= value:
                # make a withdrawal and adjust the local record
                self.contract.withdraw_from(value, {'from': address})
                self.deposits[address] -= value
            else:
                # attempting to withdraw beyond your balance should revert
                with brownie.reverts("Insufficient balance"):
                    self.contract.withdraw_from(value, {'from': address})

        def invariant(self):
            # compare the contract deposit amounts with the local record
            for address, amount in self.deposits.items():
                assert self.contract.deposited(address) == amount


    def test_stateful(Depositer, accounts, state_machine):
        state_machine(StateMachine, accounts, Depositer)

When this test is executed, it will call ``rule_deposit`` and ``rule_withdraw`` using random data from the given strategies until it encounters a state which violates one of the assertions. If this happens, it repeats the test in an attempt to find the shortest path and smallest data set possible that reproduces the error. Finally it saves the failing conditions to be used in future tests, and then delivers the following output:

::

        def invariant(self):
            for address, amount in self.deposits.items():
    >           assert self.contract.deposited(address) == amount
    E           AssertionError: assert 0 == 1

    Falsifying example:
    state = BrownieStateMachine()
    state.rule_deposit(address=<Account '0x33A4622B82D4c04a53e170c638B944ce27cffce3'>, value=1)
    state.rule_withdraw(address=<Account '0x33A4622B82D4c04a53e170c638B944ce27cffce3'>, value=0)
    state.teardown()

From this we can see the sequence of calls leading up to the error, and that the failed assertion is that ``self.contract.deposited(address)`` is zero, when we expected it to be one. We can infer that the contract is incorrectly adjusting balances within the withdraw function. Looking at that function:

.. code-block:: python
    :lineno-start: 9

    @external
    def withdraw_from(_value: uint256) -> bool:
        assert self.deposited[msg.sender] >= _value, "Insufficient balance"
        self.deposited[msg.sender] = _value
        send(msg.sender, _value)
        return True

On line 12, rather than subtracting ``_value``, the balance is being *set* to ``_value``. We found the bug!

More Examples
-------------

Here are some links to repositories that make use of stateful testing. If you have a project that you would like included here, feel free to `edit this document <https://github.com/eth-brownie/brownie/edit/master/docs/tests-hypothesis-stateful.rst>`_ and open a pull request, or let us know about it on `Gitter <https://gitter.im/eth-brownie/community>`_.

    * `celioggr/erc20-pbt <https://github.com/celioggr/erc20-pbt/tree/master>`_ : A testing framework based in Property-based testing for assessing the correctness and compliance of ERC-20 contracts.
    * `iamdefinitelyahuman/NFToken <https://github.com/iamdefinitelyahuman/nftoken/tree/master/tests/stateful>`_: A non-fungible implementation of the ERC20 standard.
    * `apguerrera/DreamFrames <https://github.com/apguerrera/DreamFrames/tree/master/tests/stateful>`_: Buy and sell frames in movies.
    * `curvefi/curve-dao-contracts <https://github.com/curvefi/curve-dao-contracts/tree/master/tests/integration>`_: Vyper contracts used by Curve DAO

Running Stateful Tests
======================

By default, stateful tests are included when you run your test suite. There is no special action required to invoke them.

You can choose to exclude stateful tests, or to *only* run stateful tests, with the ``--stateful`` flag. This can be useful to split the test suite when setting up `continuous integration <https://github.com/brownie-mix/github-actions-mix>`_.

To only run stateful tests:

::

    $ brownie test --stateful true

To skip stateful tests:

::

    $ brownie test --stateful false

When a stateful test is active the console shows a spinner that rotates each time a run of the test has finished. If the color changes from yellow to red, it means the test has failed and hypothesis is now searching for the shortest path to the failure.
