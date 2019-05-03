.. _coverage:

======================
Checking Test Coverage
======================

.. warning:: Test coverage evaluation is still under development. There may be undiscovered issues, particularly cases where conditional True/False evaluation is incorrect. Use common sense when viewing coverage reports and please open an issue on github if you encounter any issues.

Test coverage is estimated by generating a map of opcodes associated with each function and line of the smart contract source code, and then analyzing the stack trace of each transaction to see which opcodes were executed.

Because calls to view and pure methods typically are not done with a transaction, you must enable the ``always_transact`` configuration setting or your coverage for these methods will show as 0%. See the test :ref:`test_settings` documentation for more information.

To check your unit test coverage, type:

::

    $ brownie test --coverage

This will run all the test scripts in the ``tests/`` folder and give an estimate of test coverage:

::

    $ brownie test --coverage
    Using network 'development'
    Running 'ganache-cli -a 20'...

    Running transfer.py - 1 test
    ✓ Deployment 'token' (0.1882s)
    ✓ Transfer tokens (0.1615s)
    Using network 'development'
    Running 'ganache-cli -a 20'...

    Running approve_transferFrom.py - 3 tests
    ✓ Deployment 'token' (0.1263s)
    ✓ Set approval (0.2016s)
    ✓ Transfer tokens with transferFrom (0.1375s)
    ✓ transerFrom should revert (0.0486s)

    Coverage analysis complete!

    contract: Token
        add - 50.0%
        allowance - 0.0%
        approve - 100.0%
        balanceOf - 0.0%
        decimals - 0.0%
        name - 0.0%
        sub - 75.0%
        symbol - 0.0%
        totalSupply - 0.0%
        transfer - 100.0%
        transferFrom - 100.0%

Brownie will output a % score for each contract method, that you can use to quickly gauge your overall coverage level.

To analyze specific test coverage, type:

::

    $ brownie gui

Or from the console:

.. code-block:: python

    >>> Gui()

This will open the Brownie GUI.  Then press ``C`` to display the coverage results.  Relevant code will be highlighted in different colors:

* Green - code was executed during the tests
* Yellow - code was executed, but only evaluated truthfully
* Orange - code was executed, but only evaluated falsely
* Red - code was not executed

.. image:: opview.png

Analysis results are saved in the ``build/coverage`` folder.
