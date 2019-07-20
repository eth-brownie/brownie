.. _api-test:

========
Test API
========

The ``test`` package contains classes and methods for running tests and evaluating test coverage.

This functionality is typically accessed via `pytest <https://docs.pytest.org/en/latest/>`_.  See :ref:`test` and :ref:`coverage`.


``brownie.test.plugin``
=======================

The ``plugin`` module contains classes and methods used in the Brownie Pytest plugin.  It defines custom fixtures and handles integration into the Pytest workflow.

Pytest Fixtures
---------------

Brownie includes the following fixtures for use with ``pytest``.

.. note:: These fixtures are only available when pytest is run from inside a Brownie project folder.


Session Fixtures
****************

These fixtures provide access to objects related to the project being tested.

.. py:attribute:: plugin.accounts

    Session scope. Yields an instantiated :ref:`Accounts<api-network-accounts>` container for the active project.

.. py:attribute:: plugin.a

    Session scope. Short form of the ``accounts`` fixture.

.. py:attribute:: plugin.history

    Session scope. Yields an instantiated :ref:`TxHistory<api-network-history>` object for the active project.

.. py:attribute:: plugin.rpc

    Session scope. Yields an instantiated :ref:`Rpc<rpc>` object.

.. py:attribute:: plugin.web3

    Session scope. Yields an instantiated :ref:`Web3<web3>` object.

Isolation Fixtures
******************

These fixtures are used to effectively isolate tests. If included on every test within a module, that module may now be skipped via the ``--update`` flag when none of the related files have changed since it was last run.

.. py:attribute:: plugin.module_isolation

    Module scope. When used, this fixture is always applied before any other module-scoped fixtures.

    Resets the local environment before starting the first test and again after completing the final test.

.. py:method:: plugin.fn_isolation(module_isolation)

    Function scope. When used, this fixture is always applied before any other function-scoped fixtures.

    Applies the ``module_isolation`` fixture, and additionally takes a snapshot prior to running each test which is then reverted to after the test completes. The snapshot is taken immediately after any module-scoped fixtures are applied, and before all function-scoped ones.

Coverage Fixtures
*****************

These fixtures alter the behaviour of tests when coverage evaluation is active.

.. py:attribute:: plugin.no_call_coverage

    Function scope. Coverage evaluation will not be performed on called contact methods during this test.

.. py:attribute:: plugin.skip_coverage

    Function scope. If coverage evaluation is active, this test will be skipped.

RevertContextManager
--------------------

The ``RevertContextManager`` closely mimics the behaviour of `pytest.raises <https://docs.pytest.org/en/latest/reference.html#pytest-raises>`_.

.. py:class:: plugin.RevertContextManager(revert_msg=None)

    Context manager used to handle ``VirtualMachineError`` exceptions. Raises ``AssertionError`` if no transaction has reverted when the context closes.

    * ``revert_msg``: Optional. Raises an ``AssertionError`` if the transaction does not revert with this error string.

    Available as ``pytest.reverts``.

    .. code-block:: python
        :linenos:

        import pytest
        from brownie import accounts

        def test_transfer_reverts(Token, accounts):
            token = accounts[0].deploy(Token, "Test Token", "TST", 18, "1000 ether")
            with pytest.reverts():
                token.transfer(account[2], "10000 ether", {'from': accounts[1]})

``brownie.test.manager``
========================

The ``manager`` module contains the ``TestManager`` class, used internally by Brownie to determine which tests should run and to load and save the test results.

``brownie.test.output``
=======================

The ``output`` module contains methods for formatting and displaying test output.

Module Methods
--------------

.. py:method:: output.save_coverage_report(coverage_eval, report_path)

    Generates and saves a test coverage report for viewing in the GUI.

    * ``coverage_eval``: Coverage evaluation dict
    * ``report_path``: Path to save to. If the path is a folder, the report is saved as ``coverage-%d%m%y.json``.

.. py:method:: output.print_gas_profile()

    Formats and prints a gas profile report.

.. py:method:: output.print_coverage_totals(coverage_eval)

    Formats and prints a coverage evaluation report.

    * ``coverage_eval``: Coverage evaluation dict

``brownie.test.coverage``
=========================

The ``coverage`` module is used internally for storing and accessing coverage evaluation data.

Module Methods
--------------

.. py:method:: coverage.add(txhash, coverage_eval)

.. py:method:: coverage.add_cached(txhash, coverage_eval)

.. py:method:: coverage.add_from_cached(txhash, active=True)

.. py:method:: coverage.get_and_clear_active()

.. py:method:: coverage.get_all()

.. py:method:: coverage.get_merged()

.. py:method:: coverage.clear()
