=================
Testing A Project
=================

Test scripts are stored in the ``tests/`` folder. To run every test at once, type:

::

    $ brownie test

You can run a specific test by giving the filename without an extension, for example:

::

    $ brownie test transfer

Test scripts should contain one or more functions. These functions may have any name and should expect no arguments. Brownie will execute every function in the script sequentially, except those where the function name begins with an underscore. You can include a docstring in the functions to give more verbosity while they run.

Tests rely heavily on functions in the Brownie ``check`` module. You can read about them in the API :ref:`api_check` documentation.

The network is reset between running each test script. Tests cannot access any state changes that occured from a previous test.

.. note:: If you do not set a default gas limit in the configuration file, ``web3.eth.estimateGas`` is called to estimate. Transactions that would cause the EVM to revert will raise a VirtualMachineError during this estimation and so will not be broadcasted. You will not have access to any information about the failed transaction.

In order to define the base contract setup, each test script should include a variable ``DEPLOYMENT`` that gives the name of a deployment script to run.

You can create as many test scripts as needed. Here is an example script from ``projects/tokens/approve_transferFrom.py``, that includes deployment and multiple test functions:

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
