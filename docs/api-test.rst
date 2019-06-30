.. _api-test:

========
Test API
========

The ``test`` package contains classes and methods for running tests and evaluating test coverage.

This functionality is typically accessed via the command line interface.  See :ref:`test` and :ref:`coverage`.

``brownie.test.main``
=====================

The ``main`` module contains higher level methods for executing a project's tests. These methods are available directly from ``brownie.test``.

.. py:method:: test.run_tests(test_path, only_update=True, check_coverage=False, gas_profile=False)

    Locates and executes tests for a project. Calling this method is equivalent to running ``brownie test`` from the CLI.

    * ``test_path``: path to locate tests in
    * ``only_update``: if ``True``, will only run tests that were not previous run or where changes to related files have occured
    * ``check_coverage``: if ``True``, test coverage will also be evaluated and a report shown in the console
    * ``gas_profile``: if ``True``, gas use data will be shown in the console

.. py:method:: test.run_script(script_path, method_name="main", args=(), kwargs={}, gas_profile=False)

    Loads a script and calls a method within it. Calling this method is equivalent to calling ``brownie run`` from the CLI.

    * ``script_path``: path of script to load
    * ``method_name``: name of method to call
    * ``args``: method args
    * ``kwargs``: method keyword arguments
    * ``gas_profile``: if ``True``, gas use data will be shown in the console

.. _api_check:

``brownie.test.check``
======================

The ``check`` module exposes the following methods that are used in place of ``assert`` when writing Brownie tests. All check methods raise an ``AssertionError`` when they fail.

.. py:method:: check.true(statement, fail_msg = "Expected statement to be True")

    Raises if ``statement`` is not ``True``.

    .. code-block:: python

        >>> check.true(True)
        >>> check.true(2 + 2 == 4)
        >>>
        >>> check.true(0 > 1)
        File "brownie/test/check.py", line 18, in true
            raise AssertionError(fail_msg)
        AssertionError: Expected statement to be True

        >>> check.true(False, "What did you expect?")
        File "brownie/test/check.py", line 18, in true
            raise AssertionError(fail_msg)
        AssertionError: What did you expect?

        >>> check.true(1)
        File "brownie/test/check.py", line 16, in true
            raise AssertionError(fail_msg+" (evaluated truthfully but not True)")
        AssertionError: Expected statement to be True (evaluated truthfully but not True)

.. py:method:: check.false(statement, fail_msg = "Expected statement to be False")

    Raises if ``statement`` is not ``False``.

    .. code-block:: python

        >>> check.false(0 > 1)
        >>> check.false(2 + 2 == 4)
        File "brownie/test/check.py", line 18, in false
            raise AssertionError(fail_msg)
        AssertionError: Expected statement to be False

        >>> check.false(0)
        File "brownie/test/check.py", line 16, in false
            raise AssertionError(fail_msg+" (evaluated falsely but not False)")
        AssertionError: Expected statement to be False (evaluated falsely but not False)

.. py:method:: check.confirms(fn, args, fail_msg = "Expected transaction to confirm")

    Performs the given contract call ``fn`` with arguments ``args``. Raises if the call causes the EVM to revert.

    Returns a ``TransactionReceipt`` instance.

    .. code-block:: python

        >>> Token[0].balanceOf(accounts[2])
        900
        >>> check.confirms(Token[0].transfer, (accounts[0], 900, {'from': accounts[2]}))

        Transaction sent: 0xc9e056550ec579ba6b842d27bb7f029912c865becce19ee077734a04d5198f8c
        Token.transfer confirmed - block: 7   gas used: 20921 (15.39%)

        >>> Token[0].balanceOf(accounts[2])
        0
        >>> check.confirms(Token[0].transfer, (accounts[0], 900, {'from': accounts[2]}))
        File "brownie/test/check.py", line 61, in confirms
            raise AssertionError(fail_msg)
        AssertionError: Expected transaction to confirm

.. py:method:: check.reverts(fn, args, revert_msg=None)

    Performs the given contract call ``fn`` with arguments ``args``. Raises if the call does not cause the EVM to revert. This check will work regardless of if the revert happens from a call or a transaction.

    .. code-block:: python

        >>> Token[0].balanceOf(accounts[2])
        900
        >>> check.reverts(Token[0].transfer, (accounts[0], 10000, {'from': accounts[2]})
        >>> check.reverts(Token[0].transfer, (accounts[0], 900, {'from': accounts[2]}))

        Transaction sent: 0xc9e056550ec579ba6b842d27bb7f029912c865becce19ee077734a04d5198f8c
        Token.transfer confirmed - block: 7   gas used: 20921 (15.39%)
        File "brownie/test/check.py", line 45, in reverts
            raise AssertionError(fail_msg)
        AssertionError: Expected transaction to revert

.. py:method:: check.event_fired(tx, name, count=None, values=None)

    Expects a transaction to contain an event.

    * ``tx``: A ``TransactionReceipt`` instance.
    * ``name``: Name of the event that must fire.
    * ``count``: Number of times the event must fire. If left as ``None``, the event must fire one or more times.
    * ``values``: A dict, or list of dicts, speficying key:value pairs that must be found within the events of the given name. The length of the ``values`` implies the number of events that must fire with that name.

    .. code-block:: python

        >>> tx = Token[0].transfer(accounts[1], 1000, {'from': accounts[0]})

        Transaction sent: 0xaf9f68a8e72764f7475263aeb11ae544d81e45516787b93cc8797b7152195a52
        Token.transfer confirmed - block: 3   gas used: 35985 (26.46%)
        <Transaction object '0xaf9f68a8e72764f7475263aeb11ae544d81e45516787b93cc8797b7152195a52'>
        >>> check.event_fired(tx, "Transfer")
        >>> check.event_fired(tx, "Transfer", count=1)
        >>> check.event_fired(tx, "Transfer", count=2)
        File "brownie/test/check.py", line 80, in event_fired
            name, count, len(events)
        AssertionError: Event Transfer - expected 2 events to fire, got 1
        >>>
        >>> check.event_fired(tx, "Transfer", values={'value': 1000})
        >>> check.event_fired(tx, "Transfer", values={'value': 2000})
        File "brownie/test/check.py", line 105, in event_fired
            name, k, v, data[k]
        AssertionError: Event Transfer - expected value to equal 2000, got 1000
        >>>
        >>> check.event_fired(tx, "Transfer", values=[{'value': 1000}, {'value': 2000}])
        File "brownie/test/check.py", line 91, in event_fired
            name, len(events), len(values)
        AssertionError: Event Transfer - 1 events fired, 2 values to match given

.. py:method:: check.event_not_fired(tx, name, fail_msg="Expected event not to fire")

    Expects a transaction not to contain an event.

    * ``tx``: A ``TransactionReceipt`` instance.
    * ``name``: Name of the event that must fire.
    * ``fail_msg``:  Message to show if check fails.

    .. code-block:: python

        >>> tx = Token[0].transfer(accounts[1], 1000, {'from': accounts[0]})

        Transaction sent: 0xaf9f68a8e72764f7475263aeb11ae544d81e45516787b93cc8797b7152195a52
        Token.transfer confirmed - block: 3   gas used: 35985 (26.46%)
        <Transaction object '0xaf9f68a8e72764f7475263aeb11ae544d81e45516787b93cc8797b7152195a52'>
        >>> check.event_not_fired(tx, "Approve")
        >>> check.event_not_fired(tx, "Transfer")
        File "brownie/test/check.py", line 80, in event_not_fired
            name, count, len(events)
        AssertionError: Expected event not to fire

.. py:method:: check.equal(a, b, fail_msg = "Expected values to be equal", strict=False)

    Raises if ``a != b``.

    Different types of sequence objects will still evaluate equally as long as their content is the same: ``(1,1,1) == [1,1,1]``.

    When ``strict`` is set to ``False`` the following will evaluate as equal:

    * hexstrings of the same value but differing leading zeros: ``0x00001234 == 0x1234``
    * integers, floats, and strings as :ref:`wei <wei>` that have the same numberic value: ``1 == 1.0 == "1 wei"``

    .. code-block:: python

        >>> t = Token[0]
        <Token Contract object '0x1F3d78dC50DbDae4D2527D2EA17D7299b90Efe50'>
        >>> t.balanceOf(accounts[0])
        10000
        >>> t.balanceOf(accounts[1])
        0
        >>> check.equal(t.balanceOf(accounts[0]), t.balanceOf(accounts[1]))
        File "brownie/test/check.py", line 74, in equal
            raise AssertionError(fail_msg)
        AssertionError: Expected values to be equal

.. py:method:: check.not_equal(a, b, fail_msg = "Expected values to be not equal", strict=False)

    Raises if ``a == b``. Comparison rules are the same as ``check.equal``.

    .. code-block:: python

        >>> t = Token[0]
        <Token Contract object '0x1F3d78dC50DbDae4D2527D2EA17D7299b90Efe50'>
        >>> t.balanceOf(accounts[1])
        0
        >>> t.balanceOf(accounts[2])
        0
        >>> check.not_equal(t.balanceOf(accounts[1]), t.balanceOf(accounts[2]))
        File "brownie/test/check.py", line 86, in not_equal
            raise AssertionError(fail_msg)
        AssertionError: Expected values to be not equal

``brownie.test.coverage``
=========================

The ``coverage`` module contains methods related to test coverage analysis.

.. py:method:: coverage.analyze(history, coverage_eval={})

    Analyzes contract coverage.

    * ``history``: List of ``TransactionReceipt`` objects.
    * ``coverage_eval``: Coverage evaluation data from a previous call to this method. If given, the results will of this call will be merged into it.

    Returns a coverage evaluation map, structured as follows. The ``index`` values are the same as the coverage indexes in the `program counter map <compile-pc-map>`_. Whenever an index is encountered during the transaction trace it is added to the coverage map.

    .. code-block:: javascript

        {
            "ContractName": {
                "statements": {
                    "path/to/file": {index, index, .. }, ..
                },
                "branches": {
                    "true": {
                        "path/to/file": {index, index, ..}, ..
                    },
                    "false": {
                        "path/to/file": {index, index, ..}, ..
                    }
                }
            }
        }

.. py:method:: coverage.merge(coverage_eval_list)

    Given a list of coverage evaluation maps, returns a single merged coverage evaluation map.

.. py:method:: coverage.merge_files(coverage_files)

    Given a list of coverage evaluation json file paths, returns a single merged coverage evaluation map.

.. py:method:: coverage.split_by_fn(coverage_eval)

    Splits a coverage evaluation map by contract function.

.. py:method:: coverage.get_totals(coverage_eval)

    Returns a modified coverage eval dict showing counts and totals for each
    contract function.

.. py:method:: coverage.get_highlights(coverage_eval)

    Given a coverage evaluation map as generated by ``coverage.analyze`` or ``coverage.merge``, returns a generic highlight report suitable for display within the Brownie GUI.

``brownie.test.executor``
=========================

The ``executor`` module contains methods used for executing test modules. It is called internally by ``main.run_tests``.

.. py:method:: executor.run_test_modules(test_paths, only_update=True, check_coverage=False, save=True)

    Runs tests across one or more modules.

    * ``test_paths``: list of test module paths
    * ``only_update``: if ``True``, will only run tests that were not previous run or where changes to related files have occured
    * ``check_coverage``: if ``True``, test coverage will also be evaluated and a report shown in the console
    * ``save``: if ``True``, test results will be saved in the ``build/tests`` folder

``brownie.test.loader``
=======================

The ``loader`` module contains methods used internally for preparing and importing test modules.

.. py:method:: loader.import_from_path(path)

    Imports a module from the given path.

    .. code-block:: python

        >>> from brownie.test.loader import import_from_path
        >>> import_from_path('scripts/token.py')
        <module 'scripts.token' from 'token/scripts/token.py'>

.. py:method:: loader.get_methods(path, coverage=False)

    Parses a module and returns information about the methods it contains. Used internally by ``executor.run_test_modules``.

    Returns a list of two item tuples. The first item is the method, the second is a `FalseyDict <api-types-falseydict>`_ of method settings extracted from its keyword arguments.

``brownie.test.output``
=======================

The ``output`` module contains classes and methods for formatting and printing test output to the console.

TestPrinter
-----------

The ``TestPrinter`` class is used by ``executor.run_test_modules`` for outputting test results.

Module Methods
--------------

.. py:method:: output.coverage_totals(coverage_eval)

    Formats and prints a coverage evaluation report to the console.

.. py:method:: output.gas_profile()

    Prints a formatted version of `TxHistory.gas_profile <api-network-history-gas-profile>`_ to the console.



``brownie.test.pathutils``
==========================

The ``pathutils`` module contains methods for working with paths related to test and script execution, and test result JSON files.

.. py:method:: pathutils.check_build_hashes(base_path)

    Checks the hash data in all test build json files, and deletes those where
    hashes have changed.

.. py:method:: pathutils.remove_empty_folders(base_path)

    Removes empty subfolders within the given path.

.. py:method:: pathutils.get_ast_hash(path)

    Generates a sha1 hash based on the AST of a script. Any projectscripts that are imported will also be included when generating the hash.

    Used to check if the functionality within a test has changed, when determining if it should be re-run.

.. py:method:: pathutils.get_path(path_str, default_folder="scripts")

    Returns a Path object for a python module. Used for finding a user-specified script.

    * ``path_str``: Path to the script. Raises ``FileNotFoundError`` if the given path is a folder.
    * ``default_folder``: default folder path to check if ``path_str`` is not found.

.. py:method:: pathutils.get_paths(path_str=None, default_folder="tests")

    Returns a list of Path objects of python modules. Used for finding a test scripts based on the given path.

    * ``path_str``: Base path to look for modules in. If given path is a folder, all scripts within the folder and it's subfolders will be returned.
    * ``default_folder``: default folder path to check if ``path_str`` is not found.

.. py:method:: pathutils.get_build_paths(test_paths)

    Given a list of test paths, returns an equivalent list of build paths.

.. py:method:: pathutils.get_build_json(test_path)

    Loads the data for a given test that has been saved in the ``build/tests`` folder. If the file cannot be found or is corrupted, creates the necessary folder structure and returns an appropriately formatted blank dict.

.. py:method:: pathutils.save_build_json(module_path, result, coverage_eval, contract_names)

    Saves the result data for a given test as a JSON in the ``build/tests`` folder.

    * ``module_path``: Path of the test module
    * ``result``: Result of the test execution (``"passing"`` or ``"failing"``)
    * ``coverage_eval``: Test coverage evaluation as a dict
    * ``contract_names``: List of contracts called by the test module during it's execution

.. py:method:: pathutils.save_report(coverage_eval, report_path)

    Saves a test coverage report for viewing in the GUI.

    * ``coverage_eval``: Coverage evaluation dict
    * ``report_path``: Path to save to. If the path is a folder, the report is saved as ``coverage-%d%m%y.json``.
