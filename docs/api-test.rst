.. _api-test:

========
Test API
========

The ``test`` package contains classes and methods for running tests and evaluating test coverage.

This functionality is typically accessed via `pytest <https://docs.pytest.org/en/latest/>`_.  See :ref:`pytest`.

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

    Session scope. Yields an instantiated :func:`Accounts <brownie.network.account.Accounts>` container for the active project.

.. py:attribute:: fixtures.a

    Session scope. Short form of the :func:`accounts <fixtures.accounts>` fixture.

.. py:attribute:: fixtures.Contract

    Session scope. Yields the :func:`Contract <brownie.network.contract.Contract>` class, used to interact with contracts outside of the active project.

.. py:attribute:: fixtures.history

    Session scope. Yields an instantiated :func:`TxHistory <brownie.network.state.TxHistory>` object for the active project.

.. py:attribute:: fixtures.rpc

    Session scope. Yields an instantiated :func:`Rpc <brownie.network.rpc.Rpc>` object.

.. py:attribute:: fixtures.state_machine

    Session scope. Yields the :func:`state_machine <stateful.state_machine>` method, used to launc rule-based state machine tests.

.. py:attribute:: fixtures.web3

    Session scope. Yields an instantiated :func:`Web3 <brownie.network.web3.Web3>` object.

Isolation Fixtures
******************

These fixtures are used to effectively isolate tests. If included on every test within a module, that module may now be skipped via the ``--update`` flag when none of the related files have changed since it was last run.

.. py:attribute:: fixtures.module_isolation

    Module scope. When used, this fixture is always applied before any other module-scoped fixtures.

    Resets the local environment before starting the first test and again after completing the final test.

.. py:method:: fixtures.fn_isolation(module_isolation)

    Function scope. When used, this fixture is always applied before any other function-scoped fixtures.

    Applies the :func:`module_isolation <fixtures.module_isolation>` fixture, and additionally takes a snapshot prior to running each test which is then reverted to after the test completes. The snapshot is taken immediately after any module-scoped fixtures are applied, and before all function-scoped ones.

``brownie.test.strategies``
===========================

The ``strategies`` module contains the :func:`strategy <strategies.strategy>` method, and related internal methods for generating Hypothesis `search strategies <https://hypothesis.readthedocs.io/en/latest/details.html#defining-strategies>`_.

.. py:method:: strategies.strategy(type_str, **kwargs)

    Returns a Hypothesis ``SearchStrategy`` based on the value of ``type_str``. Depending on the type of strategy, different ``kwargs`` are available.

    See the :ref:`hypothesis-strategies` section for information on how to use this method.

``brownie.test.stateful``
=========================

The ``stateful`` module contains the :func:`state_machine <stateful.state_machine>` method, and related internal classes and methods for performing `stateful testing <https://hypothesis.readthedocs.io/en/latest/stateful.html>`_.

.. py:method:: stateful.state_machine(state_machine_class, *args, settings=None, **kwargs)

    Executes a stateful test.

    * ``state_machine_class``: A state machine class to be used in the test. Be sure to pass the class itself, not an instance of the class.
    * ``*args``: Any arguments given here will be passed to the state machine's ``__init__`` method.
    * ``settings``: An optional dictionary of :ref:`Hypothesis settings<hypothesis-settings>` that will replace the defaults for this test only.

    See the :ref:`hypothesis-stateful` section for information on how to use this method.

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

    ``xdist`` runner plugin manager. Inherits from :func:`PytestBrownieRunner <manager.runner.PytestBrownieRunner>`.

.. py:class:: manager.master.PytestBrownieMaster

    ``xdist`` master plugin manager.

RevertContextManager
--------------------

The ``RevertContextManager`` behaves similarly to :func:`pytest.raises <pytest.raises>`.

.. py:class:: brownie.test.plugin.RevertContextManager(revert_msg=None, dev_revert_msg=None, revert_pattern=None, dev_revert_pattern=None)

    Context manager used to handle :func:`VirtualMachineError <brownie.exceptions.VirtualMachineError>` exceptions. Raises ``AssertionError`` if no transaction has reverted when the context closes.

    * ``revert_msg``: Optional. Raises if the transaction does not revert with this error string.
    * ``dev_revert_msg``: Optional. Raises if the transaction does not revert with this :ref:`dev revert string<dev-revert>`.
    * ``revert_pattern``: Regex pattern to compare against the transaction error string. Raises if the error string does not fully match the regex (partial matches are not allowed).
    * ``dev_revert_pattern``: Regex pattern to compare against the transaction dev revert string.

    This class is available as ``brownie.reverts`` when ``pytest`` is active.

    .. code-block:: python
        :linenos:

        import brownie

        def test_transfer_reverts(Token, accounts):
            token = accounts[0].deploy(Token, "Test Token", "TST", 18, 1e23)
            with brownie.reverts():
                token.transfer(account[2], 1e24, {'from': accounts[1]})

``brownie.test.output``
=======================

The ``output`` module contains methods for formatting and displaying test output.

Internal Methods
----------------

.. py:method:: output._save_coverage_report(build, coverage_eval, report_path)

    Generates and saves a test coverage report for viewing in the GUI.

    * ``build``: Project :func:`Build <brownie.project.build.Build>` object
    * ``coverage_eval``: Coverage evaluation dict
    * ``report_path``: Path to save to. If the path is a folder, the report is saved as ``coverage.json``.

.. py:method:: output._print_gas_profile()

    Formats and prints a gas profile report. The report is grouped by contracts and functions are sorted by average gas used.

.. py:method:: output._print_coverage_totals(build, coverage_eval)

    Formats and prints a coverage evaluation report.

    * ``build``: Project :func:`Build <brownie.project.build.Build>` object
    * ``coverage_eval``: Coverage evaluation dict

.. py:method:: output._get_totals(build, coverage_eval)

    Generates an aggregated coverage evaluation dict that holds counts and totals for each contract function.

    * ``build``: Project :func:`Build <brownie.project.build.Build>` object
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

    * ``build``: Project :func:`Build <brownie.project.build.Build>` object
    * ``coverage_eval``: Coverage evaluation dict

    * Original format: ``{"path/to/file": [index, ..], .. }``
    * Returned format: ``{"path/to/file": { "ContractName.functionName": [index, .. ], .. }``

.. py:method:: output._get_highlights(build, coverage_eval)

    Returns a highlight map formatted for display in the GUI.

    * ``build``: Project :func:`Build <brownie.project.build.Build>` object
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
