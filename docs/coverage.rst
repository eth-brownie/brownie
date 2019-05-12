.. _coverage:

======================
Checking Test Coverage
======================

.. warning:: Test coverage evaluation is still under development. There may be undiscovered issues, particularly cases where conditional ``True``/``False`` evaluation is incorrect. Use common sense when viewing coverage reports and please open an issue on github if you encounter any issues.

Test coverage is estimated by generating a map of opcodes associated with each function and line of the smart contract source code, and then analyzing the stack trace of each transaction to see which opcodes were executed.

During analysis, all contract calls are executed as transactions. This gives a more accurate coverage picture by allowing analysis of methods that are typically non-state changing.  Whenever one of these calls-as-transactions results in a state change, the blockchain will be reverted to ensure that the outcome of the test is not effected. For tests that involve many calls this can result in significantly slower execution time. You can prevent this behaviour by adding ``always_transact=False`` as a keyword argument for a test.

To check your unit test coverage, type:

::

    $ brownie test --coverage

This will run all the test scripts in the ``tests/`` folder and give an estimate of test coverage:

::

    $ brownie test --coverage
    Brownie v1.0.0 - Python development framework for Ethereum

    Using solc version v0.5.7

    Running transfer.py - 1 test
    ✓ 0 - setup (0.1882s)
    ✓ 1 - Transfer tokens (0.1615s)
    ✓ 2 - Evaluating test coverage (0.0009s)

    Running approve_transferFrom.py - 3 tests
    ✓ 0 - setup (0.1263s)
    ✓ 1 - Set approval (0.2016s)
    ✓ 2 - Transfer tokens with transferFrom (0.1375s)
    ✓ 3 - transerFrom should revert (0.0486s)
    ✓ 4 - Evaluating test coverage (0.0026s)

    SUCCESS: All tests passed.

    Coverage analysis complete!

      contract: Token
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

    Coverage report saved at reports/coverage-010170.json

Brownie will output a % score for each contract method, that you can use to quickly gauge your overall coverage level. A coverage report is also saved in the project's ``reports`` folder.

.. _coverage-gui:

Brownie GUI
===========

For an in-depth look at your test coverage, type:

::

    $ brownie gui

Or from the console:

.. code-block:: python

    >>> Gui()

This will open the Brownie GUI. In the upper right drop boxes, select a contract to view and then choose the generated coverage report JSON. Relevant code will be highlighted in different colors:

* Green - code was executed during the tests
* Yellow - code was executed, but only evaluated truthfully
* Orange - code was executed, but only evaluated falsely
* Red - code was not executed

.. image:: opview.png

Analysis results are saved in the ``build/coverage`` folder.
