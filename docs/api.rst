.. _api:

===========
Brownie API
===========



.. _api_check:

Check
=====

The check module exposes the following methods that are used in place of ``assert`` when writing Brownie tests.

.. py:method:: check.true(statement, fail_msg = "Expected statement to be true")

    Raises if ``statement`` does not evaluate to True.

.. py:method:: check.false(statement, fail_msg = "Expected statement to be False")

    Raises if ``statement`` does not evaluate to False.

.. py:method:: check.reverts(fn, args, fail_msg = "Expected transaction to revert")

    Performs the given contract call ``fn`` with arguments ``args``. Raises if the call does not cause the EVM to revert.

.. py:method:: check.confirms(fn, args, fail_msg = "Expected transaction to confirm")

    Performs the given contract call ``fn`` with arguments ``args``. Raises if the call causes the EVM to revert.

    This method is useful if you want to give a specific error message for this function. If you do not require one, you can simply attempt the call and the test will still fail if the call reverts.

.. py:method:: check.equal(a, b, fail_msg = "Expected values to be equal")

    Raises if ``a != b``.

.. py:method:: check.not_equal(a, b, fail_msg = "Expected values to be not equal")

    Raises if ``a == b``.
