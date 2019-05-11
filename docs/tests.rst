
.. _test:

============
Unit Testing
============

Test scripts are stored in the ``tests/`` folder. To run every test at once, type:

::

    $ brownie test

For larger projects you can also store tests within subfolders and point Brownie to run only a specific folder. Brownie will skip any file or folder that begins with an underscore.

To run a specific test or folder of tests, enter the path without an extension:

::

    $ brownie test transfer

.. hint::

    Each time a test runs, Brownie saves hashes of the bytecode for each contract it interacts with. It also saves a hash from the AST of the test file and any imported scripts. If you include the ``--update`` flag when running tests, Brownie will regenerate these hashes and only run the ones where changes have occured.

Running Tests
=============

When running tests, the sequence of events is as follows:

* Brownie checks for a method named ``setup``. If it exists it is called.

* A snapshot of the EVM is taken.

* Each method within the module is called sequentially. Methods with a name beginning in an understore are ignored. All functionality within a method is collectively considered 1 test, if an exception is raised at any time the test terminates and is considered to have failed.

* The EVM is reverted to the snapshot in between calling each method.

* After the final method has completed the test RPC is restarted, configuration settings are reset, the next script is loaded and the process begins again.

Writing Tests
=============

As with scripts, every test should begin with ``from brownie import *`` in order to give access to the :ref:`api`. You can also import and execute scripts as a part of your setup process.

You can define unique configuration settings for each test by modifying the ``config`` dictionary in the ``setup`` method. Any changes that you make are reset when the test completes.

You can optionally include a docstring in each test method to give more verbosity during the testing process.

The following keyword arguments can be used to affect how a test runs:

* ``skip``: If set to ``True``, this test will not be run. If set to ``coverage``, the test will only be skipped during coverage evaluation.
* ``pending``: If set to ``True``, this test is expected to fail. If the test passes it will raise an ``ExpectedFailing`` exception.
* ``always_transact``: If set to ``False``, calls to non state-changing methods will still execute as calls when running test coverage analysis. See :ref:`coverage` for more information.

Any arguments applied to a test module's ``setup`` method will be used as the default arguments for all that module's methods. Including ``skip=True`` on the setup method will skip the entire module.

Tests rely heavily on methods in the Brownie ``check`` module as an alternative to normal ``assert`` statements. You can read about them in the API :ref:`api_check` documentation.

Example Test Script
===================

Here is an example test script from ``projects/token/tests/approve_transferFrom.py`` that includes setup, multiple tests methods, docstrings, and use of the pending and skipped kwargs:

.. code-block:: python

    from brownie import *
    import scripts.token


    def setup():
        scripts.token.main()
        global token
        token = Token[0]


    def balance(skip=True):
        check.equal(
            token.balanceOf(accounts[0], "1000 ether"),
            "Accounts 0 balance is wrong"
        )


    def approve():
        '''Set approval'''
        token.approve(accounts[1], "10 ether", {'from': accounts[0]})
        check.equal(
            token.allowance(accounts[0], accounts[1]),
            "10 ether",
            "Allowance is wrong"
        )
        check.equal(
            token.allowance(accounts[0], accounts[2]),
            0,
            "Allowance is wrong"
        )
        token.approve(accounts[1], "6 ether", {'from': accounts[0]})
        check.equal(
            token.allowance(accounts[0], accounts[1]),
            "6 ether",
            "Allowance is wrong"
        )


    def transfer():
        '''Transfer tokens with transferFrom'''
        token.approve(accounts[1], "6 ether", {'from': accounts[0]})
        token.transferFrom(
            accounts[0],
            accounts[2],
            "5 ether",
            {'from': accounts[1]}
        )
        check.equal(
            token.balanceOf(accounts[2]),
            "5 ether",
            "Accounts 2 balance is wrong"
        )
        check.equal(
            token.balanceOf(accounts[1]),
            0,
            "Accounts 1 balance is wrong"
        )
        check.equal(
            token.balanceOf(accounts[0]),
            "995 ether",
            "Accounts 0 balance is wrong"
        )
        check.equal(
            token.allowance(accounts[0], accounts[1]),
            "1 ether",
            "Allowance is wrong"
        )


    def revert():
        '''transerFrom should revert'''
        check.reverts(
            token.transferFrom,
            (accounts[0], accounts[3], "10 ether", {'from': accounts[1]})
        )
        check.reverts(
            token.transferFrom,
            (accounts[0], accounts[2], "1 ether", {'from': accounts[0]})
        )


    def unfinished(pending=True):
        '''This test is expected to fail'''
        token.secretFunction(accounts[1], "10 ether")

Below you can see an example of the output from Brownie when the test script executes. For the example, one of the tests was modified so that it would fail.

::

    $ brownie test approve_transferFrom
    Brownie v1.0.0 - Python development framework for Ethereum

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

For available classes and methods when writing a test script, see the :ref:`api-test` documentation.

.. _test_settings:

Settings and Considerations
===========================

The following test configuration settings are available in ``brownie-config.json``.  These settings will affect the behaviour of your tests.

.. code-block:: javascript

    {
        "test": {
            "gas_limit": 6721975,
            "default_contract_owner": false
        }
    }

.. py:attribute:: default_contract_owner

    If ``True``, calls to contract transactions that do not specify a sender are broadcast from the same address that deployed the contract.

    If ``False``, contracts will not remember which account they were created by. You must explicitely declare the sender of every transaction with a `transaction parameters <https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.sendTransaction>`__ dictionary as the last method argument. This may be considered similar to a strict mode.
