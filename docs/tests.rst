
.. _test:

====================
Testing Your Project
====================

Test scripts are stored in the ``tests/`` folder. To run every test at once, type:

::

    $ brownie test

You can run a specific test by giving the filename without an extension, for example:

::

    $ brownie test transfer

For larger projects you can also store tests within subfolders, and point Brownie to run only a specific folder. Brownie will skip any file or folder that begins with an underscore.

Running Tests
=============

When running tests, the sequence of events is as follows:

* First, brownie checks for a method named ``setup``. If it exists it is called.

* A snapshot of the EVM is taken.

* Each method within the module is called sequentially. Methods with a name beginning in an understore are ignored. All functionality within a method is collectively considered 1 test, if an exception is raised at any time the test is considered to have failed.

* The EVM is reverted to the snapshot in between calling each method.

* After the final method has completed the test RPC is restarted, configuration settings are reset, the next script is loaded and the process begins again.

Writing Tests
=============

As with scripts, every test should begin with ``from brownie import *`` in order to give access to the :ref:`api`. You can also import and execute scripts as a part of your setup process.

You can define unique configuration settings for each test by modifying the ``config`` dictionary in the ``setup`` method. Any changes that you make are reset when the test completes.

You can optionally include a docstring in each test method to give more verbosity during the testing process.

The following keyword arguments can be used to affect how a test runs:

* ``pending``: If set to True, this test is expected to fail. If the test passes it will raise an ``ExpectedFailing`` exception.

* ``skip``: If set to True, this test will not be run.

Tests rely heavily on methods in the Brownie ``check`` module as an alternative to normal ``assert`` statements. You can read about them in the API :ref:`api_check` documentation.

Example Test Script
===================

Here is an example test script from ``projects/token/tests/approve_transferFrom.py`` that includes setup, multiple tests methods, docstrings, and use of the pending and skipped kwargs:

.. literalinclude:: ../projects/token/tests/approve_transferFrom.py
    :linenos:
    :language: python
    :lines: 3-

Below you can see an example of the output from Brownie when the test script executes. For the example, one of the tests was modified so that it would fail.

::

    $ brownie test approve_transferFrom
    Brownie v0.9.0b - Python development framework for Ethereum

    Using network 'development'
    Running 'ganache-cli'...
    Compiling contracts...
    Optimizer: Enabled  Runs: 200
    - Token.sol...
    - SafeMath.sol...

    Running approve_transferFrom.py - 5 tests
    ✓ setup (0.1416s)
    ⊝ balance (skipped)
    ✓ Set approval (0.5330s)
    ✗ Transfer tokens with transferFrom (AssertionError)
    ✓ transerFrom should revert (0.2066s)
    ‼ This test is expected to fail (AttributeError)

    WARNING: 1 test failed.

    Exception info for tests/approve_transferFrom.transfer:
    File "tests/approve_transferFrom.py", line 53, in transfer
        "Accounts 2 balance is wrong"
    AssertionError: Accounts 2 balance is wrong: 5000000000000000000 != 1000000000000000000

For available classes and methods when writing a test script, see the :ref:`api` documentation.

.. _test_settings:

Settings and Considerations
===========================

The following test configuration settings are available in ``brownie-config.json``.  These settings will affect the behaviour of your tests.

.. code-block:: javascript

    {
        "test": {
            "always_transact": true,
            "gas_limit": 65000000,
            "default_contract_owner": false
        }
    }

.. py:attribute:: always_transact

    If set to ``true``:

    * Methods with a state mutability of ``view`` or ``pure`` are still called as a transaction
    * Calls will consume gas, increase the block height and the nonce of the caller.
    * You may supply a transaction dictionary as the last argument as you would with any other transaction.
    * You will still be returned the return value of the transaction, not a ``TransactionReceipt``.

    If set to ``false``:

    * Methods will be called with the normal behaviour.
    * Test coverage will report 0% for all ``view`` and ``pure`` methods.

.. py:attribute:: gas_limit

    If set to an integer, this value will over-ride the default gas limit setting for whatever network you are testing on.

    When the gas limit is calculated automatically:

    * Transactions that would cause the EVM to revert will raise a ``VirtualMachineError`` during gas estimation and so will not be broadcasted.
    * No ``TransactionReceipt`` is generated. You will not have access to any information about why it failed.

    When the gas limit is a fixed value:

    * Transactions that revert will be broadcasted, but still raise a ``VirtualMachineError``.
    * Unless the call is handled with ``check.reverts`` the exception will cause the test to fail.
    * If you need to access the ``TransactionReceipt`` you can find it the ``history`` list.

.. py:attribute:: default_contract_owner

    If ``True``, calls to contract transactions that do not specify a sender are broadcast from the same address that deployed the contract.

    If ``False``, contracts will not remember which account they were created by. You must explicitely declare the sender of every transaction with a `transaction parameters <https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.sendTransaction>`__ dictionary as the last method argument. This may be considered similar to a strict mode.
