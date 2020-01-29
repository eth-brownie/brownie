.. _api-test:

========
Test API
========

The ``test`` package contains classes and methods for running tests and evaluating test coverage.

This functionality is typically accessed via `pytest <https://docs.pytest.org/en/latest/>`_.  See :ref:`test`.

``brownie.test.fixtures``
=========================

The ``fixtures`` module contains custom fixtures provided by the Brownie Pytest plugin.

Pytest Fixtures
---------------

.. note:: These fixtures are only available when ``pytest`` is run from inside a Brownie project folder.

Session Fixtures
****************

These fixtures provide access to objects related to the project being tested.

.. py:attribute:: fixtures.accounts

    Session scope. Yields an instantiated :ref:`Accounts<api-network-accounts>` container for the active project.

.. py:attribute:: fixtures.a

    Session scope. Short form of the ``accounts`` fixture.

.. py:attribute:: fixtures.history

    Session scope. Yields an instantiated :ref:`TxHistory<api-network-history>` object for the active project.

.. py:attribute:: fixtures.rpc

    Session scope. Yields an instantiated :ref:`Rpc<rpc>` object.

.. py:attribute:: fixtures.state_machine

    Session scope. Yields the :ref:`state_machine<api-test-state_machine>` method, used to launc rule-based state machine tests.

.. py:attribute:: fixtures.web3

    Session scope. Yields an instantiated :ref:`Web3<web3>` object.

Isolation Fixtures
******************

These fixtures are used to effectively isolate tests. If included on every test within a module, that module may now be skipped via the ``--update`` flag when none of the related files have changed since it was last run.

.. py:attribute:: fixtures.module_isolation

    Module scope. When used, this fixture is always applied before any other module-scoped fixtures.

    Resets the local environment before starting the first test and again after completing the final test.

.. py:method:: fixtures.fn_isolation(module_isolation)

    Function scope. When used, this fixture is always applied before any other function-scoped fixtures.

    Applies the ``module_isolation`` fixture, and additionally takes a snapshot prior to running each test which is then reverted to after the test completes. The snapshot is taken immediately after any module-scoped fixtures are applied, and before all function-scoped ones.

Coverage Fixtures
*****************

These fixtures alter the behaviour of tests when coverage evaluation is active.

.. py:attribute:: fixtures.no_call_coverage

    Function scope. Coverage evaluation will not be performed on called contact methods during this test.

.. py:attribute:: fixtures.skip_coverage

    Function scope. If coverage evaluation is active, this test will be skipped.

``brownie.test.strategies``
===========================

The ``strategies`` module contains the ``strategy`` method, and related internal methods for generating Hypothesis `search strategies <https://hypothesis.readthedocs.io/en/latest/details.html#defining-strategies>`_.

.. py:method:: strategies.strategy(type_str, **kwargs)

    Returns a Hypothesis ``SearchStrategy`` based on the value of ``type_str``. Depending on the type of strategy, different ``kwargs`` are available.

``brownie.test.stateful``
=========================

The ``stateful`` module contains the ``state_machine`` method, and related internal classes and methods for performing `stateful testing <https://hypothesis.readthedocs.io/en/latest/stateful.html>`_.

.. _api-test-state_machine:

.. py:method:: stateful.state_machine(rules_object, *args, settings=None, **kwargs)

    Run a state machine definition as a test.

    * ``rules_object``: An uninitialized state machine class.
    * ``settings``: Optional dictionary of values used to create a Hypothesis `settings <https://hypothesis.readthedocs.io/en/latest/settings.html#available-settings>`_ object.

    ``args`` and ``kwargs`` are passed to the ``__init__`` method of ``rules_object`` during the setup phase of the test.

``brownie.test.plugin``
=======================

The ``plugin`` module is the entry point for the Brownie pytest plugin. It contains two ``pytest`` hook point methods that are used for setting up the plugin. The majority of the plugin functionality is handled by a :ref:`plugin manager<api-test-plugin-manager>` which is instantiated in the ``pytest_configure`` method.

``brownie.test.manager``
========================

The ``manager`` module contains Brownie classes used internally to manage the Brownie pytest plugin.

.. _api-test-plugin-manager:

Plugin Managers
---------------

One of these classes is instantiated in the ``pytest_configure`` method of ``brownie.test.plugin``. Which is used depends on whether or not `pytest-xdist <https://github.com/pytest-dev/pytest-xdist>`_ is active.

.. py:class:: manager.base.PytestBrownieBase

    Base class that is inherited by all Brownie plugin managers.

.. py:class:: manager.runner.PytestBrownieRunner

    Runner plugin manager, used when ``xdist`` is not active.

.. py:class:: manager.runner.PytestBrownieXdistRunner

    ``xdist`` runner plugin manager. Inherits from ``PytestBrownieRunner``.

.. py:class:: manager.master.PytestBrownieMaster

    ``xdist`` master plugin manager.

RevertContextManager
--------------------

The ``RevertContextManager`` closely mimics the behaviour of `pytest.raises <https://docs.pytest.org/en/latest/reference.html#pytest-raises>`_.

.. py:class:: plugin.RevertContextManager(revert_msg=None)

    Context manager used to handle ``VirtualMachineError`` exceptions. Raises ``AssertionError`` if no transaction has reverted when the context closes.

    * ``revert_msg``: Optional. Raises an ``AssertionError`` if the transaction does not revert with this error string.

    This class is available as ``brownie.reverts`` when ``pytest`` is active.

    .. code-block:: python
        :linenos:

        import brownie

        def test_transfer_reverts(Token, accounts):
            token = accounts[0].deploy(Token, "Test Token", "TST", 18, "1000 ether")
            with brownie.reverts():
                token.transfer(account[2], "10000 ether", {'from': accounts[1]})

``brownie.test.output``
=======================

The ``output`` module contains methods for formatting and displaying test output.

Internal Methods
----------------

.. py:method:: output._save_coverage_report(build, coverage_eval, report_path)

    Generates and saves a test coverage report for viewing in the GUI.

    * ``build``: Project :ref:`api-project-build-build` object
    * ``coverage_eval``: Coverage evaluation dict
    * ``report_path``: Path to save to. If the path is a folder, the report is saved as ``coverage.json``.

.. py:method:: output._print_gas_profile()

    Formats and prints a gas profile report.

.. py:method:: output._print_coverage_totals(build, coverage_eval)

    Formats and prints a coverage evaluation report.

    * ``build``: Project :ref:`api-project-build-build` object
    * ``coverage_eval``: Coverage evaluation dict

.. py:method:: output._get_totals(build, coverage_eval)

    Generates an aggregated coverage evaluation dict that holds counts and totals for each contract function.

    * ``build``: Project :ref:`api-project-build-build` object
    * ``coverage_eval``: Coverage evaluation dict

    Returns:

    .. code-block:: python

        { "ContractName": {
            "statements": {
                "path/to/file": {
                    "ContractName.functionName": (count, total), ..
                }, ..
            },
            "branches" {
                "path/to/file": {
                    "ContractName.functionName": (true_count, false_count, total), ..
                }, ..
            }
        }

.. py:method:: output._split_by_fn(build, coverage_eval)

    Splits a coverage eval dict so that coverage indexes are stored by contract function. The returned dict is no longer compatible with other methods in this module.

    * ``build``: Project :ref:`api-project-build-build` object
    * ``coverage_eval``: Coverage evaluation dict

    * Original format: ``{"path/to/file": [index, ..], .. }``
    * Returned format: ``{"path/to/file": { "ContractName.functionName": [index, .. ], .. }``

.. py:method:: output._get_highlights(build, coverage_eval)

    Returns a highlight map formatted for display in the GUI.

    * ``build``: Project :ref:`api-project-build-build` object
    * ``coverage_eval``: Coverage evaluation dict

    Returns:

    .. code-block:: python

        {
            "statements": {
                "ContractName": {"path/to/file": [start, stop, color, msg], .. },
            },
            "branches": {
                "ContractName": {"path/to/file": [start, stop, color, msg], .. },
            }
        }

    See :ref:`gui-report-json` for more info on the return format.

``brownie.test.coverage``
=========================

The ``coverage`` module is used storing and accessing coverage evaluation data.

Module Methods
--------------

.. py:method:: coverage.get_coverage_eval()

    Returns all coverage data, active and cached.

.. py:method:: coverage.get_merged_coverage_eval()

    Merges and returns all active coverage data as a single dict.

.. py:method:: coverage.clear()

    Clears all coverage eval data.

Internal Methods
----------------

.. py:method:: coverage.add_transaction(txhash, coverage_eval)

    Adds coverage eval data.

.. py:method:: coverage.add_cached_transaction(txhash, coverage_eval)

    Adds coverage data to the cache.

.. py:method:: coverage.check_cached(txhash, active=True)

    Checks if a transaction hash is present within the cache, and if yes includes it in the active data.

.. py:method:: coverage.get_active_txlist()

    Returns a list of coverage hashes that are currently marked as active.

.. py:method:: coverage.clear_active_txlist()

    Clears the active coverage hash list.
