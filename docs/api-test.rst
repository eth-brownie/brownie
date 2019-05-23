.. _api-test:

========
Test API
========

``brownie.test``
================

The ``test`` package contains classes and methods for running tests and evaluating test coverage.

.. _api_check:

``brownie.test.check``
======================

The ``check`` module exposes the following methods that are used in place of ``assert`` when writing Brownie tests. All check methods raise an ``AssertionError`` when they fail.

Module Methods
--------------

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

The ``coverage`` module contains methods related to test coverage analysis. These methods are called via ``cli.test`` and the Brownie GUI, they are not meant to be called directly.

Module Methods
--------------

.. py:method:: coverage.analyze_coverage(history)

    Given a list of ``TransactionReceipt`` objects, returns a coverage report.

.. py:method:: coverage.merge_coverage(coverage_files)

    Given a list of coverage file paths, returns a single aggregated coverage report.

.. py:method:: coverage.generate_report(coverage_eval)


    Given a coverage report as generated by ``analyze_coverage`` or ``merge_coverage``, returns a generic highlight report suitable for display within the Brownie GUI.
