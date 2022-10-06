
.. _pytest:

==================
Writing Unit Tests
==================

Brownie utilizes the ``pytest`` framework for unit testing. Pytest is a mature, feature-rich test framework. It lets you write small tests with minimal code, scales well for large projects, and is highly extendable.

To run your tests:

::

    $ brownie test

This documentation provides a quick overview of basic pytest usage, with an emphasis on features that are relevent to Brownie. Many components of pytest are only explained partially - or not at all. If you wish to learn more about pytest you should review the official `pytest documentation <https://docs.pytest.org/en/latest/>`_.

Getting Started
===============

Test File Structure
-------------------

Pytest performs a `test discovery <https://docs.pytest.org/en/latest/goodpractices.html#test-discovery>`_ process to locate functions that should be included in your project's test suite.

    1. Tests must be stored within the ``tests/`` directory of your project, or a subdirectory thereof.
    2. Filenames must match ``test_*.py`` or ``*_test.py``.

Within the test files, the following methods will be run as tests:

    1. Functions outside of a class prefixed with ``test``.
    2. Class methods prefixed with ``test``, where the class is prefixed with ``Test`` and does not include an ``__init__`` method.

Writing your First Test
-----------------------

The following example is a very simple test using Brownie and pytest, verifying that an account balance has correctly changed after performing a transaction.

.. code-block:: python
    :linenos:

    from brownie import accounts

    def test_account_balance():
        balance = accounts[0].balance()
        accounts[0].transfer(accounts[1], "10 ether", gas_price=0)

        assert balance - "10 ether" == accounts[0].balance()

.. _pytest-fixtures-docs:

Fixtures
========

A `fixture <http://docs.pytest.org/en/latest/fixture.html>`_ is a function that is applied to one or more test functions, and is called prior to the execution of each test. Fixtures are used to setup the initial conditions required for a test.

Fixtures are declared using the :func:`@pytest.fixture <pytest.fixture>` decorator. To pass a fixture to a test, include the fixture name as an input argument for the test:

.. code-block:: python
    :linenos:

    import pytest

    from brownie import Token, accounts

    @pytest.fixture
    def token():
        return accounts[0].deploy(Token, "Test Token", "TST", 18, 1000)

    def test_transfer(token):
        token.transfer(accounts[1], 100, {'from': accounts[0]})
        assert token.balanceOf(accounts[0]) == 900

In this example the ``token`` fixture is called prior to running ``test_transfer``. The fixture returns a deployed :func:`Contract <brownie.network.contract.ProjectContract>` instance which is then used in the test.

Fixtures can also be included as dependencies of other fixtures:

.. code-block:: python
    :linenos:

    import pytest

    from brownie import Token, accounts

    @pytest.fixture
    def token():
        return accounts[0].deploy(Token, "Test Token", "TST", 18, 1000)

    @pytest.fixture
    def distribute_tokens(token):
        for i in range(1, 10):
            token.transfer(accounts[i], 100, {'from': accounts[0]})

Brownie Pytest Fixtures
-----------------------

Brownie provides fixtures that simplify interacting with and testing your project. Most core Brownie functionality can be accessed via a fixture rather than an import statement. For example, here is the previous example using Brownie fixtures rather than imports:

.. code-block:: python
    :linenos:

    import pytest

    @pytest.fixture
    def token(Token, accounts):
        return accounts[0].deploy(Token, "Test Token", "TST", 18, 1000)

    def test_transfer(token, accounts):
        token.transfer(accounts[1], 100, {'from': accounts[0]})
        assert token.balanceOf(accounts[0]) == 900

See the :ref:`pytest-fixtures-reference` for information about all available fixtures.

Fixture Scope
-------------

The default behaviour for a fixture is to execute each time it is required for a test. By adding the ``scope`` parameter to the decorator, you can alter how frequently the fixture executes. Possible values for scope are: ``function``, ``class``, ``module``, or ``session``.

Expanding upon our example:

.. code-block:: python
    :linenos:

    import pytest

    @pytest.fixture(scope="module")
    def token(Token):
        return accounts[0].deploy(Token, "Test Token", "TST", 18, 1000)

    def test_approval(token, accounts):
        token.approve(accounts[1], 500, {'from': accounts[0]})
        assert token.allowance(accounts[0], accounts[1]) == 500

    def test_transfer(token, accounts):
        token.transfer(accounts[1], 100, {'from': accounts[0]})
        assert token.balanceOf(accounts[0]) == 900

By applying a ``module`` scope to the the ``token`` fixture, the contract is only deployed once and the same :func:`Contract <brownie.network.contract.ProjectContract>` instance is used for both ``test_approval`` and ``test_transfer``.

Fixture of higher-scopes (such as ``session`` or ``module``) are always instantiated before lower-scoped fixtures (such as ``function``). The relative order of fixtures of same scope follows the declared order in the test function and honours dependencies between fixtures. The only exception to this rule is isolation fixtures, which are expained below.


.. _pytest-fixtures-isolation:

Isolation Fixtures
------------------

In many cases you will want isolate your tests from one another by resetting the local environment. Without isolation, it is possible that the outcome of a test will be dependent on actions performed in a previous test.

Brownie provides two fixtures that are used to handle isolation:

    * :func:`module_isolation <fixtures.module_isolation>` is a module scoped fixture. It resets the local chain before and after completion of the module, ensuring a clean environment for this module and that the results of it will not affect subsequent modules.
    * :func:`fn_isolation <fixtures.fn_isolation>` is function scoped. It additionally takes a snapshot of the chain before running each test, and reverts to it when the test completes. This allows you to define a common state for each test, reducing repetitive transactions.

Isolation fixtures are **always the first fixture within their scope to execute**. You can be certain that any action performed within a fuction-scoped fixture will happen `after` the isolation snapshot.

To apply an isolation fixture to all tests in a module, require it in another fixture and include the ``autouse`` parameter:

.. code-block:: python
    :linenos:

    import pytest

    @pytest.fixture(scope="module", autouse=True)
    def shared_setup(module_isolation):
        pass

You can also place this fixture in a `conftest.py <https://docs.pytest.org/en/latest/fixture.html#conftest-py-sharing-fixtures-across-multiple-files>`_ file to apply it across many modules.

Defining a Shared Initial State
-------------------------------

A common pattern is to include one or more module-scoped setup fixtures that define the initial test conditions, and then use :func:`fn_isolation <fixtures.fn_isolation>` to revert to this base state at the start of each test. For example:

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

1. The setup phase of :func:`module_isolation <fixtures.module_isolation>` runs, resetting the local environment.
2. The module-scoped ``token`` fixture runs, deploying a ``Token`` contract with a total supply of 1000 tokens.
3. The setup phase of the function-scoped :func:`fn_isolation <fixtures.fn_isolation>` fixture runs. A snapshot of the blockchain is taken.
4. ``test_transfer`` runs, transferring 100 tokens from ``accounts[0]`` to ``accounts[1]``
5. The teardown phase of :func:`fn_isolation <fixtures.fn_isolation>` runs. The blockchain is reverted to it's state before ``test_transfer``.
6. The setup phase of the :func:`fn_isolation <fixtures.fn_isolation>` fixture runs again. Another snapshot is taken - identical to the previous one.
7. ``test_chain_reverted`` runs. The assert statement passes because of the :func:`fn_isolation <fixtures.fn_isolation>` fixture.
8. The teardown phase of :func:`fn_isolation <fixtures.fn_isolation>` runs. The blockchain is reverted to it's state before ``test_chain_reverted``.
9. The teardown phase of :func:`module_isolation <fixtures.module_isolation>` runs, resetting the local environment.

.. _pytest-markers-docs:

Markers
=======

A `marker <https://docs.pytest.org/en/stable/mark.html#mark>`_ is a decorator applied to a test function. Markers are used to pass meta data about the test which is accessible by fixtures and plugins.

To apply a marker to a specific test, use the :func:`@pytest.mark <pytest.mark>` decorator:

.. code-block:: python
    :linenos:

    @pytest.mark.foo
    def test_with_example_marker():
        pass

To apply markers at the module level, add the ``pytestmark`` global variable:

.. code-block:: python
    :linenos:

    import pytest

    pytestmark = [pytest.mark.foo, pytest.mark.bar]

Along with the standard `pytest markers <https://docs.pytest.org/en/latest/reference.html#marks>`_, Brownie provides additional markers specific to smart contract testing. See the :ref:`markers reference<pytest-fixtures-reference-markers>` section of the documentation for more information.



Handling Reverted Transactions
==============================

When running tests, transactions that revert raise a :func:`VirtualMachineError <brownie.exceptions.VirtualMachineError>` exception. To write assertions around this you can use :func:`brownie.reverts <brownie.test.plugin.RevertContextManager>` as a context manager. It functions very similarly to :func:`pytest.raises <pytest.raises>`.

.. code-block:: python
    :linenos:

    import brownie

    def test_transfer_reverts(accounts, Token):
        token = accounts[0].deploy(Token, "Test Token", "TST", 18, 1e23)
        with brownie.reverts():
            token.transfer(accounts[1], 1e24, {'from': accounts[0]})

You may optionally include a string as an argument. If given, the error string returned by the transaction must match it in order for the test to pass.

.. code-block:: python
    :linenos:

    import brownie

    def test_transfer_reverts(accounts, Token):
        token = accounts[0].deploy(Token, "Test Token", "TST", 18, 1e23)
        with brownie.reverts("Insufficient Balance"):
            token.transfer(accounts[1], 1e24, {'from': accounts[0]})

.. _dev-revert:

Developer Revert Comments
-------------------------

Each revert string adds a minimum 20000 gas to your contract deployment cost, and increases the cost for a function to execute. Including a revert string for every ``require`` and ``revert`` statement is often impractical and sometimes simply not possible due to the block gas limit.

For this reason, Brownie allows you to include revert strings as source code comments that are not included in the bytecode but still accessible via :func:`TransactionReceipt.revert_msg <TransactionReceipt.revert_msg>`. You write tests that target a specific ``require`` or ``revert`` statement without increasing gas costs.

Revert string comments must begin with ``// dev:`` in Solidity, or ``# dev:`` in Vyper. Priority is always given to compiled revert strings. Some examples:

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

When there is an error string included in the code, you can still access the dev revert reason via :func:`TransactionReceipt.dev_revert_msg <TransactionReceipt.dev_revert_msg>`:

.. code-block:: python

    >>> tx = test.revertExamples(4)
    Transaction sent: 0xd9e0fb1bd6532f6aec972fc8aef806a8d8b894349cf5c82c487335625db8d0ef
    test.revertExamples confirmed (cannot be four) - block: 3   gas used: 31337 (6.66%)
    <Transaction object '0xd9e0fb1bd6532f6aec972fc8aef806a8d8b894349cf5c82c487335625db8d0ef'>

    >>> tx.revert_msg
    'cannot be four'

    >>> tx.dev_revert_msg
    'dev: is four'

Parametrizing Tests
===================

The ``@pytest.mark.parametrize`` marker enables `parametrization of arguments <http://docs.pytest.org/en/latest/parametrize.html>`_ for a test function. Here is a typical example of a parametrized test function, checking that a certain input results in an expected output:

.. code-block:: python
    :linenos:

    import pytest

    @pytest.mark.parametrize('amount', [0, 100, 500])
    def test_transferFrom_reverts(token, accounts, amount):
        token.approve(accounts[1], amount, {'from': accounts[0]})
        assert token.allowance(accounts[0], accounts[1]) == amount

In the example the ``@parametrize`` decorator defines three different values for ``amount``. The ``test_transferFrom_reverts`` is executed three times using each of them in turn.

You can achieve a similar effect with the ``@given`` decorator to automatically generate parametrized tests from a defined range:

.. code-block:: python
    :linenos:

    from brownie.test import given, strategy

    @given(amount=strategy('uint', max_value=1000))
    def test_transferFrom_reverts(token, accounts, amount):
        token.approve(accounts[1], amount, {'from': accounts[0]})
        assert token.allowance(accounts[0], accounts[1]) == amount

This technique is known as `property-based testing`. To learn more, read :ref:`hypothesis`.

.. _pytest-other-projects:

Testing against Other Projects
==============================

The ``pm`` fixture provides access to packages that have been installed with the :ref:`Brownie package manager<package-manager>`. Using this fixture, you can write test cases that verify interactions between your project and another project.

``pm`` is a function that accepts a project ID as an argument and returns a :func:`Project <brownie.project.main.Project>` object. This way you can deploy contracts from the package and deliver them as fixtures to be used in your tests:

.. code-block:: python
    :linenos:

    @pytest.fixture(scope="module")
    def compound(pm, accounts):
        ctoken = pm('defi.snakecharmers.eth/compound@1.1.0').CToken
        yield ctoken.deploy({'from': accounts[0]})

Be sure to add required testing packages to your project :ref:`dependency list<package-manager-deps>`.

Running Tests
=============

To run the complete test suite:

::

    $ brownie test

Or to run a specific test:

::

    $ brownie test tests/test_transfer.py

Test results are saved at ``build/tests.json``. This file holds the results of each test, coverage analysis data, and hashes that are used to determine if any related files have changed since the tests last ran. If you abort test execution early via a ``KeyboardInterrupt``, results are only saved for modules that fully completed.

Only Running Updated Tests
--------------------------

After the test suite has been run once, you can use the ``--update`` flag to only repeat tests where changes have occured:

::

    $ brownie test --update

A module must use the :func:`module_isolation <fixtures.module_isolation>` or :func:`fn_isolation <fixtures.fn_isolation>` fixture in every test function in order to be skipped in this way.

The ``pytest`` console output will represent skipped tests with an ``s``, but it will be colored green or red to indicate if the test passed when it last ran.

If coverage analysis is also active, tests that previously completed but were not analyzed will be re-run.  The final coverage report will include results for skipped modules.

Brownie compares hashes of the following items to check if a test should be re-run:

* The bytecode for every contract deployed during execution of the test
* The AST of the test module
* The AST of all ``conftest.py`` modules that are accessible to the test module

.. _pytest-interactive:

Interactive Debugging
---------------------

The ``--interactive`` flag allows you to debug your project while running your tests:

::

    $ brownie test --interactive

When using interactive mode, Brownie immediately prints the traceback for each failed test and then opens a console. You can interact with the deployed contracts and examine the transaction history to help determine what went wrong.

* Deployed :func:`ProjectContract <brownie.network.contract.ProjectContract>` objects are available within their associated :func:`ContractContainer <brownie.network.contract.ContractContainer>`
* :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` objects are in the :func:`TxHistory <brownie.network.state.TxHistory>` container, available as ``history``
* Use :func:`chain.undo <Chain.undo>` and :func:`chain.redo <Chain.redo>` to move backward and forward through recent transactions

Once you are finished, type ``quit()`` to continue with the next test.

See :ref:`Inspecting and Debugging Transactions <core-transactions>` for more information on Brownie's debugging functionality.

Evaluating Gas Usage
--------------------

To generate a gas profile report, add the ``--gas`` flag:

::

    $ brownie test --gas

When the tests complete, a report will display:

::

        Gas Profile:
        Token <Contract>
           ├─ constructor   -  avg: 1099591  low: 1099591  high: 1099591
           ├─ transfer      -  avg:   43017  low:   43017  high:   43017
           └─ approve       -  avg:   21437  low:   21437  high:   21437
        Storage <Contract>
           ├─ constructor   -  avg:  211445  low:  211445  high:  211445
           └─ set           -  avg:   21658  low:   21658  high:   21658

Evaluating Coverage
-------------------

To check your unit test coverage, add the ``--coverage`` flag:

::

    $ brownie test --coverage

When the tests complete, a report will display:

::

    contract: Token - 80.8%
      Token.allowance - 100.0%
      Token.approve - 100.0%
      Token.balanceOf - 100.0%
      Token.transfer - 100.0%
      Token.transferFrom - 100.0%
      SafeMath.add - 75.0%
      SafeMath.sub - 75.0%
      Token.<fallback> - 0.0%

    Coverage report saved at reports/coverage.json

Brownie outputs a % score for each contract method that you can use to quickly gauge your overall coverage level. A detailed coverage report is also saved in the project's ``reports`` folder, that can be viewed via the Brownie GUI. See :ref:`coverage-gui` for more information.

You can exclude specific contracts or source files from this report by modifying your project's :ref:`configuration file <config-reports>`.

.. _xdist:

Using ``xdist`` for Distributed Testing
---------------------------------------

Brownie is compatible with the `pytest-xdist <https://github.com/pytest-dev/pytest-xdist>`_ plugin, allowing you to parallelize test execution. In large test suites this can greatly reduce the total runtime.

You may wish to read an overview of `how xdist works <https://github.com/pytest-dev/pytest-xdist/blob/master/OVERVIEW.md>`_ if you are unfamiliar with the plugin.

To run your tests in parralel, include the ``-n`` flag:

::

    $ brownie test -n auto

Tests are distributed to workers on a per-module basis. An :ref:`isolation fixture<pytest-fixtures-isolation>` must be applied to every test being executed, or ``xdist`` will fail after collection. This is because without proper isolation it is impossible to ensure consistent behaviour between test runs.
