
.. _test:

========================
Unit Testing with Pytest
========================


Brownie utilizes the ``pytest`` framework for unit testing. You may wish to view the `pytest documentation <https://docs.pytest.org/en/latest/>`_ if you have not used it previously.

Test scripts are stored in the ``tests/`` folder of your project. To run the complete test suite:

::

    $ pytest tests


Brownie Pytest Fixtures
=======================

Brownie provides `pytest fixtures <https://docs.pytest.org/en/latest/fixture.html>`_ which allow you to interact with your project. To use a fixture, add an argument with the same name to the inputs of your test function.

Session Fixtures
----------------

These fixtures provide quick access to Brownie objects that are frequently used during testing. If you are unfamiliar with these objects, you may wish to read :ref:`interaction`.

.. py:attribute:: accounts

    Yields an :ref:`Accounts<api-network-accounts>` container for the active project, used to interact with your local Eth accounts.

    .. code-block:: python
        :linenos:

        def test_account_balance(accounts):
            assert accounts[0].balance() == "100 ether"

.. py:attribute:: a

    Short form of the ``accounts`` fixture.

    .. code-block:: python
        :linenos:

        def test_account_balance(a):
            assert a[0].balance() == "100 ether"

.. py:attribute:: history

    Yields a :ref:`TxHistory<api-network-history>` container for the active project, used to access transaction data.

    .. code-block:: python
        :linenos:

        def test_account_balance(accounts, history):
            accounts[0].transfer(accounts[1], "10 ether")
            assert len(history) == 1

.. py:attribute:: rpc

    Yields an :ref:`Rpc<rpc>` object, used for interacting with the local test chain.

    .. code-block:: python
        :linenos:

        def test_account_balance(accounts, rpc):
            balance = accounts[1].balance()
            accounts[0].transfer(accounts[1], "10 ether")
            assert accounts[1].balance() == balance + "10 ether"
            rpc.reset()
            assert accounts[1].balance() == balance

.. py:attribute:: web3

    Yields a :ref:`Web3<web3>` object.

    .. code-block:: python
        :linenos:

        def test_account_balance(accounts, web3):
            height = web3.eth.blockNumber
            accounts[0].transfer(accounts[1], "10 ether")
            assert web3.eth.blockNumber == height + 1

If you are accessing the same object across many tests in the same module, you may prefer to import it from the ``brownie`` package instead of accessing it via fixtures. The following two examples will work identically:

.. code-block:: python
    :linenos:

    def test_account_balance(accounts):
        assert accounts[0].balance() == "100 ether"

    def test_account_nonce(accounts):
        assert accounts[0].nonce == 0

.. code-block:: python
    :linenos:

    from brownie import accounts

    def test_account_balance():
        assert accounts[0].balance() == "100 ether"

    def test_account_nonce():
        assert accounts[0].nonce == 0

Contract Fixtures
-----------------

Brownie creates dynamically named fixtures to access each :ref:`api-network-contractcontainer` object within a project. Fixtures are generated for all deployable contracts and libraries.

For example - if your project contains a contract named ``Token``, there will be a ``Token`` fixture available.

.. code-block:: python
    :linenos:

    from brownie import accounts

    def test_token_deploys(Token):
        token = accounts[0].deploy(Token, "Test Token", "TST", 18, "1000 ether")
        assert token.name() == "Test Token"


Handling Reverted Transactions
==============================

When running tests, transactions that revert raise a ``VirtualMachineError`` exception. To write assertions around this you can use ``pytest.reverts`` as a context manager. It functions very similarly to `pytest.raises <https://docs.pytest.org/en/latest/assert.html#assertraises>`_.


.. code-block:: python
    :linenos:

    import pytest

    def test_transfer_reverts(Token):
        token = accounts[0].deploy(Token, "Test Token", "TST", 18, "1000 ether")
        with pytest.reverts():
            token.transfer(accounts[1], "2000 ether", {'from': accounts[0]})

You may optionally supply a string as an argument. If given, the error string returned by the transaction must match it in order for the test to pass.

.. code-block:: python
    :linenos:

    import pytest

    def test_transfer_reverts(Token):
        token = accounts[0].deploy(Token, "Test Token", "TST", 18, "1000 ether")
        with pytest.reverts("Insufficient Balance"):
            token.transfer(accounts[1], "9001 ether", {'from': accounts[0]})

.. _dev-revert:

Developer Revert Comments
-------------------------

Each revert string adds a minimum 20000 gas to your contract deployment cost, and increases the cost for a function to execute. Including a revert string for every ``require`` and ``revert`` statement is often impractical and sometimes simply not possible due to the block gas limit.

For this reason, Brownie allows you to include revert strings as source code comments that are not included in the bytecode but still accessible via ``TransactionReceipt.revert_msg``. You write tests that target a specific ``require`` or ``revert`` statement without increasing gas costs.

Revert string comments must begin with ``// dev:`` in order for Brownie to recognize them. Priority is always given to compiled revert strings. Some examples:

.. code-block:: solidity
    :linenos:

    function revertExamples(uint a) external {
        require(a != 2, "is two");
        require(a != 3); // dev: is three
        require(a != 4, "cannot be four"); // dev: is four
        require(a != 5); // is five
    }

* Line 2 will use the given revert string ``"is two"``
* Line 3 will substitute in the string supplied on the comments: ``"dev: is three"``
* Line 4 will use the given string ``"cannot be four"`` and ignore the subsitution string.
* Line 5 will have no revert string. The comment did not begin with ``"dev:"`` and so is ignored.

If the above function is executed in the console:

.. code-block:: python

    >>> tx = test.revertExamples(3)
    Transaction sent: 0xd31c1c8db46a5bf2d3be822778c767e1b12e0257152fcc14dcf7e4a942793cb4
    test.revertExamples confirmed (dev: is three) - block: 2   gas used: 31337 (6.66%)
    <Transaction object '0xd31c1c8db46a5bf2d3be822778c767e1b12e0257152fcc14dcf7e4a942793cb4'>

    >>> tx.revert_msg
    'dev: is three'

Isolating Tests
===============

Module Isolation
----------------

In most cases you will want to isolate your tests from one another by resetting the local environment in between modules. Brownie provides the ``module_isolation`` fixture to accomplish this.  This fixture calls ``Rpc.reset()`` before and after completion of the module, ensuring a clean environment for this module and that the results of it will not affect subsequent modules.

The ``module_isolation`` fixture is **always the first module-scoped fixture to execute**.

To apply the fixture to all tests in a module, include the following fixture within the module:

.. code-block:: python
    :linenos:

    import pytest

    @pytest.fixture(scope="module", autouse=True)
    def setup(module_isolation):
        pass


You can also place this fixture in a `conftest.py <https://docs.pytest.org/en/latest/fixture.html#conftest-py-sharing-fixture-functions>`_ file to apply it across many modules.

Function Isolation
------------------

Brownie provides the function scoped ``fn_isolation`` fixture, used to isolate individual test functions. This fixture takes a snapshot of the local environment before running each test, and revert to it after the test completes.

In the example below, the assert statement in ``test_isolated`` passes because the state is reverted in between tests.  If you remove the ``isolation`` fixture the test will fail.

.. code-block:: python
    :linenos:

    import pytest

    @pytest.fixture(autouse=True)
    def isolation(fn_isolation):
        pass

    def test_transfer(accounts):
        accounts[0].transfer(accounts[1], "10 ether")
        assert accounts[1].balance() == "110 ether"

    def test_isolated(accounts):
        assert accounts[1].balance() == "100 ether"

Defining a Shared Initial State
-------------------------------

The ``fn_isolation`` fixture is **always the first function-scoped fixture to execute**. A common pattern is to include one or more module-scoped setup fixtures that define the initial test conditions, and then use ``fn_isolation`` to revert to this base state at the start of each test. For example:

.. code-block:: python
    :linenos:

    import pytest

    @pytest.fixture(scope="module", autouse=True)
    def token(Token, accounts):
        t = accounts[0].deploy(Token, "Test Token", "TST", 18, 1000)
        yield t

    @pytest.fixture(autouse=True)
    def isolation(fn_isolation):
        pass

    def test_transfer(token, accounts):
        token.transfer(accounts[1], 100, {'from': accounts[0]})
        assert token.balanceOf(accounts[0]) == 900

    def test_chain_reverted(token):
        assert token.balanceOf(accounts[0]) == 1000

The sequence of events in the above example is:

1. The setup phase of ``module_isolation`` runs, resetting the local environment.
2. The module-scoped ``token`` fixture runs, deploying a ``Token`` contract with a total supply of 1000 tokens.
3. The setup phase of the function-scoped ``fn_isolation`` fixture runs. A snapshot of the blockchain is taken.
4. ``test_transfer`` runs, transferring 100 tokens from ``accounts[0]`` to ``accounts[1]``
5. The teardown phase of ``fn_isolation`` runs. The blockchain is reverted to it's state before ``test_transfer``.
6. The setup phase of the ``fn_isolation`` fixture runs again. Another snapshot is taken - identical to the previous one.
7. ``test_chain_reverted`` runs. The assert statement passes because of the ``fn_isolation`` fixture.
8. The teardown phase of ``fn_isolation`` runs. The blockchain is reverted to it's state before ``test_chain_reverted``.
9. The teardown phase of ``module_isolation`` runs, resetting the local environment.

Additionally, remember that **module-scoped fixtures will always execute prior to function-scoped**. New module-scoped fixtures can be introduced part way through a module, and in this way modify the setup snapshot. Expanding on the previous example:

.. code-block:: python
    :linenos:

    import pytest

    @pytest.fixture(scope="module", autouse=True)
    def token(Token, accounts):
        t = accounts[0].deploy(Token, "Test Token", "TST", 18, 1000)
        yield t

    @pytest.fixture(scope="module")
    def transfer_tokens(token, accounts):
        token.transfer(accounts[1], 100, {'from': accounts[0]})

    @pytest.fixture(autouse=True)
    def isolation(fn_isolation):
        pass

    def test_transfer(token, accounts):
        token.transfer(accounts[1], 100, {'from': accounts[0]})
        assert token.balanceOf(accounts[0]) == 900

    def test_chain_reverted(token):
        assert token.balanceOf(accounts[0]) == 1000

    def test_module_fixture_transfer(transfer_tokens, token):
        token.transfer(accounts[1], 50, {'from': accounts[0]})
        assert token.balanceOf(accounts[0]) == 850

    def test_snapshot_altered(token):
        assert token.balanceOf(accounts[0]) == 900

Let's look at the sequence of events, starting from the teardown of ``test_chain_reverted`` (step 8 in the previous example):

8. The teardown phase of ``fn_isolation`` runs. The blockchain is reverted to it's state before ``test_chain_reverted``.
9. The module-scoped ``transfer_tokens`` fixture runs. 100 tokens are transferred to ``accounts[1]``.
10. The setup phase of ``fn_isolation`` runs. A new snapshot is taken, this time including the transfer performed by ``transfer_tokens``.
11. ``test_module_fixture_transfer`` runs. 50  tokens are transferred and the assert statement passes.
12. The teardown phase of ``fn_isolation`` runs. The state is reverted to immediately before ``test_module_fixture_transfer`` was run.
13. The setup phase of ``fn_isolation`` runs. Another snapshot is taken - identical to the previous one.
14. ``test_snapshot_altered`` runs. The assertion passes.
15. ``fn_isolation`` and then ``module_isolation`` perform their final teardowns. The local environment is reset and the module is completed.

.. _test-coverage:

Coverage Evaluation
===================

Test coverage is calculated by generating a map of opcodes associated with each statement and branch of the source code, and then analyzing the stack trace of each transaction to see which opcodes executed. See `"Evaluating Solidity Code Coverage via Opcode Tracing" <https://medium.com/coinmonks/brownie-evaluating-solidity-code-coverage-via-opcode-tracing-a7cf5a92d28c>`_ for a more detailed explanation of how coverage evaluation works.

During coverage analysis, all contract calls are executed as transactions. This gives a more accurate coverage picture by allowing analysis of methods that are typically non-state changing. A snapshot is taken before each of these calls-as-transactions and the state is reverted immediately after, to ensure that the outcome of the test is not affected. For tests that involve many calls this can result in significantly slower execution time.

.. note::

    Coverage analysis is stored on a per-transaction basis. If you repeat an identical transaction, Brownie will not have to analyze it. It is good to keep this in mind when designing setup fixtures, especially for large test suites.

Coverage Fixtures
-----------------

Brownie provides fixtures that allow you to alter the behaviour of tests when coverage evaluation is active. They are useful for tests with many repetitive functions, to avoid the slowdown caused by ``debug_traceTransaction`` queries.

Both of these fixtures are function-scoped.

.. py:attribute:: no_call_coverage

    Coverage evaluation will not be performed on called contact methods during this test.

    .. code-block:: python
        :linenos:

        import pytest

        @pytest.fixture(scope="module", autouse=True)
        def token(Token, accounts):
            t = accounts[0].deploy(Token, "Test Token", "TST", 18, 1000)
            t.transfer(accounts[1], 100, {'from': accounts[0]})
            yield t

        def test_normal(token):
            # this call is handled as a transaction, coverage is evaluated
            assert token.balanceOf(accounts[0]) == 900

        def test_no_call_cov(Token, no_call_coverage):
            # this call happens normally, no coverage evaluation
            assert token.balanceOf(accounts[1]) == 100

.. py:attribute:: skip_coverage

    This test will be skipped if coverage evaluation is active.

Running Tests
=============

Test scripts are stored in the ``tests/`` folder. Test discovery follows the standard pytest `discovery rules <https://docs.pytest.org/en/latest/goodpractices.html#test-discovery>`_.

To run the complete test suite:

::

    $ pytest tests

Or to run a specific test:

::

    $ pytest tests/test_transfer.py

.. note::

    Because of Brownie's dynamically named contract fixtures, you cannot run ``pytest`` outside of the Brownie project folder.

Test results are saved at ``build/tests.json``. This file holds the results of each test, coverage analysis data, and hashes that are used to determine if any related files have changed since the tests last ran. If you abort test execution early via a ``KeyboardInterrupt``, results are only be saved for modules that fully completed.

Only Running Updated Tests
--------------------------

After the test suite has been run once, you can use the ``--update`` flag to only repeat tests where changes have occured:

::

    $ pytest tests --update

A module must use the ``module_isolation`` or ``fn_isolation`` fixture in every test function in order to be skipped in this way.

The ``pytest`` console output will represent skipped tests with an "s", but it will be colored green or red to indicate if the test passed when it last ran.

If coverage analysis is also active, tests that previously completed but were not analyzed will be re-run.  The final coverage report will include results for skipped modules.

Brownie compares hashes of the following items to check if a test should be re-run:

* The bytecode for every contract deployed during execution of the test
* The AST of the test module
* The AST of all ``conftest.py`` modules that are accessible to the test module

Evaluating Coverage
-------------------

To check your unit test coverage, add the ``--coverage`` flag when running pytest:

::

    $ pytest tests/ --coverage

When the tests complete, a report will display:

::

    Coverage analysis:

      contract: Token - 82.3%
        SafeMath.add - 66.7%
        SafeMath.sub - 100.0%
        Token.<fallback> - 0.0%
        Token.allowance - 100.0%
        Token.approve - 100.0%
        Token.balanceOf - 100.0%
        Token.decimals - 0.0%
        Token.name - 100.0%
        Token.symbol - 0.0%
        Token.totalSupply - 100.0%
        Token.transfer - 85.7%
        Token.transferFrom - 100.0%

    Coverage report saved at reports/coverage.json

Brownie outputs a % score for each contract method that you can use to quickly gauge your overall coverage level. A detailed coverage report is also saved in the project's ``reports`` folder, that can be viewed via the Brownie GUI. See :ref:`coverage-gui` for more information.

.. _test_settings:

Configuration Settings
======================

The following test configuration settings are available in ``brownie-config.yaml``. These settings affect the behaviour of your tests.

.. code-block:: yaml

    pytest:
        gas_limit: 6721975
        default_contract_owner: false
        reverting_tx_gas_limit: 6721975
        revert_traceback: false

.. py:attribute:: gas_limit

    Replaces the default network gas limit.

.. py:attribute:: reverting_tx_gas_limit

    Replaces the default network setting for the gas limit on a tx that will revert.

.. py:attribute:: default_contract_owner

    If ``True``, calls to contract transactions that do not specify a sender are broadcast from the same address that deployed the contract.

    If ``False``, contracts will not remember which account they were created by. You must explicitely declare the sender of every transaction with a `transaction parameters <https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.sendTransaction>`__ dictionary as the last method argument.

.. py:attribute:: revert_traceback

    If ``True``, unhandled ``VirtualMachineError`` exceptions will include a full transaction traceback. This is useful for debugging but slows test execution.

    This can also be enabled from the command line with the ``--revert-tb`` flag.
