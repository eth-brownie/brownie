=================
Testing A Project
=================

Test scripts are stored in the ``tests/`` folder. To run every test at once, type:

::

    $ brownie test

You can run a specific test by giving the filename without an extension, for example:

::

    $ brownie test transfer

When running a test script, brownie will first check for a method named ``setup`` and execute it if it exists. Then a snapshot of the EVM is taken. This snapshot is returned to between each subsequent test.

Once initial test conditions are set, every function in the module is called sequentially. Functions with a name beginning in an underscore are ignored. All commands within a function a collectively considered 1 test, if an unhandled exception is raised at any time the test is considered to have failed.

You can include docstrings in the functions to give more verbosity while they run.

Tests rely heavily on functions in the Brownie ``check`` module. You can read about them in the API :ref:`api_check` documentation.

The test RPC is fully reset between running each script. Tests cannot access any state changes that occured from a previous test.

.. note:: If you do not set a default gas limit in the configuration file, ``web3.eth.estimateGas`` is called to estimate. Transactions that would cause the EVM to revert will raise a VirtualMachineError during this estimation and so will not be broadcasted. You will not have access to any information about the failed transaction.

As with scripts, every test should begin with ``from brownie import *``, in order to give access to the :ref:`api`. You can also import and execute scripts as a part of your setup process.

You can create as many tests as needed. Here is an example script from ``projects/token/tests/approve_transferFrom.py``, that includes setup and multiple tests:

.. literalinclude:: ../projects/token/tests/approve_transferFrom.py
    :linenos:
    :language: python
    :lines: 3-


Below you can see an example of the output from Brownie when the test script executes. For the example, one of the tests was modified so that it would fail.

::

    $ brownie test approve_transferFrom
    Using network 'development'
    Running 'ganache-cli -a 20'...
    Compiling contracts...
    Optimizer: Enabled   Runs: 200

    Running approve_transferFrom.py - 3 tests
    ✓ Deployment 'token' (0.1317s)
    ✓ Set approval (0.1717s)
    ✗ Transfer tokens with transferFrom (AssertionError)
    ✓ transerFrom should revert (0.0461s)

    WARNING: 1 test failed.

    Exception info for approve_transferFrom.transfer:
    File "brownie/projects/token/tests/approve_transferFrom.py", line 18, in transfer
        check.equal(token.balanceOf(accounts[2]), "1 ether", "Accounts 2 balance is wrong")
    AssertionError: Accounts 2 balance is wrong: 5000000000000000000 != 1000000000000000000

For available classes and methods when writing a test script, see the :ref:`api` documentation.
