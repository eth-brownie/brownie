.. _core-types:

==================
Brownie Data Types
==================

Brownie provides several custom data types to simplify working with Ether values.

Wei
===

Brownie uses the :func:`Wei <brownie.convert.datatypes.Wei>` class when a value is meant to represent an amount of ether. :func:`Wei <brownie.convert.datatypes.Wei>` is a subclass of ``int`` that converts strings, scientific notation and hex strings into wei denominated integers:

.. code-block:: python

    >>> Wei("1 ether")
    1000000000000000000
    >>> Wei("12.49 gwei")
    12490000000
    >>> Wei("0.029 shannon")
    29000000
    >>> Wei(8.38e32)
    838000000000000000000000000000000

It also converts other values to :func:`Wei <brownie.convert.datatypes.Wei>` before performing comparisons, addition or subtraction:

    >>> Wei(1e18) == "1 ether"
    True
    >>> Wei("1 ether") < "2 ether"
    True
    >>> Wei("1 ether") - "0.75 ether"
    250000000000000000

Whenever a Brownie method takes an input referring to an amount of ether, the given value is converted to :func:`Wei <brownie.convert.datatypes.Wei>`. Balances and ``uint``/``int`` values returned in contract calls and events are given in :func:`Wei <brownie.convert.datatypes.Wei>`.

.. code-block:: python

    >>> accounts[0].balance()
    100000000000000000000
    >>> type(accounts[0].balance())
    <class 'brownie.convert.Wei'>
