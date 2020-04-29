.. _core-types:

==========
Data Types
==========

Brownie uses custom data types to simplify working with common represented values.

Wei
===

The :func:`Wei <brownie.convert.datatypes.Wei>` class is used when a value is meant to represent an amount of Ether. It is a subclass of :py:class:`int <int>` capable of converting strings, scientific notation and hex strings into wei denominated integers:

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

Fixed
=====

The :func:`Fixed <brownie.convert.datatypes.Fixed>` class is used to handle Vyper `decimal values <https://vyper.readthedocs.io/en/latest/types.html#decimals>`_. It is a subclass of :py:class:`decimal.Decimal <decimal.Decimal>` that allows comparisons, addition and subtraction against strings, integers and :func:`Wei <brownie.convert.datatypes.Wei>`.

.. code-block:: python

    >>> Fixed(1)
    Fixed('1')
    >>> Fixed("3.1337")
    Fixed('3.1337')
    >>> Fixed("12.49 gwei")
    Fixed('12490000000')
    >>> Fixed("-1.23") == "-1.2300"
    True


Attempting to assign, compare or perform arithmetic against a float raises a :class:`TypeError`.

.. code-block:: python

    >>> Fixed(3.1337)
    Traceback (most recent call last):
        File "<console>", line 1, in <module>
    TypeError: Cannot convert float to decimal - use a string instead

    >>> Fixed("-1.23") == -1.2300
    Traceback (most recent call last):
        File "<console>", line 1, in <module>
    TypeError: Cannot compare to floating point - use a string instead
