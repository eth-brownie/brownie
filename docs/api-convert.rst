.. _api-convert:

===========
Convert API
===========

The ``convert`` package contains methods and classes for representing and converting data.

.. _type-conversions:

``brownie.convert.main``
========================

The ``main`` module contains methods for data conversion. Methods within this module can all be imported directly from the ``convert`` package.

.. py:method:: brownie.convert.to_uint(value, type_str="uint256")

    Converts a value to an unsigned integer. This is equivalent to calling :func:`Wei <brownie.convert.datatypes.Wei>` and then applying checks for over/underflows.

.. py:method:: brownie.convert.to_int(value, type_str="int256")

    Converts a value to a signed integer. This is equivalent to calling :func:`Wei <brownie.convert.datatypes.Wei>` and then applying checks for over/underflows.

.. py:method:: brownie.convert.to_decimal(value)

    Converts a value to a decimal fixed point and applies bounds according to `Vyper's decimal type <https://vyper.readthedocs.io/en/latest/types.html#decimals>`_.

.. py:method:: brownie.convert.to_bool(value)

    Converts a value to a boolean. Raises ``ValueError`` if the given value does not match a value in ``(True, False, 0, 1)``.

.. py:method:: brownie.convert.to_address(value)

    Converts a value to a checksummed address. Raises ``ValueError`` if ``value`` cannot be converted.

.. py:method:: brownie.convert.to_bytes(value, type_str="bytes32")

    Converts a value to bytes. ``value`` can be given as bytes, a hex string, or an integer.

    Raises ``OverflowError`` if the length of the converted value exceeds that specified by ``type_str``.

    Pads left with ``00`` if the length of the converted value is less than that specified by ``type_str``.

    .. code-block:: python

        >>> from brownie.convert import to_bytes
        >>> to_bytes('0xff','bytes')
        b'\xff'
        >>> to_bytes('0xff','bytes16')
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff'

.. py:method:: brownie.convert.to_string(value)

    Converts a value to a string.

.. _type-classes:

``brownie.convert.datatypes``
=============================

The ``datatypes`` module contains subclasses that Brownie uses to assist with conversion and comparison.

EthAddress
----------

.. py:class:: brownie.convert.datatypes.EthAddress(value)

    String subclass for address comparisons. Raises a ``TypeError`` when compared to a non-address.

    Addresses returned from a contract call or as part of an event log are given in this type.

    .. code-block:: python

        >>> from brownie.convert import EthAddress
        >>> e = EthAddress("0x0035424f91fd33084466f402d5d97f05f8e3b4af")
        '0x0035424f91Fd33084466f402d5d97f05f8E3b4af'
        >>> e == "0x3506424F91fD33084466F402d5D97f05F8e3b4AF"
        False
        >>> e == "0x0035424F91fD33084466F402d5D97f05F8e3b4AF"
        True
        >>> e == "0x35424F91fD33084466F402d5D97f05F8e3b4AF"
        Traceback (most recent call last):
          File "<console>", line 1, in <module>
        TypeError: Invalid type for comparison: '0x35424F91fD33084466F402d5D97f05F8e3b4AF' is not a valid address

        >>> e == "potato"
        Traceback (most recent call last):
          File "<console>", line 1, in <module>
        TypeError: Invalid type for comparison: 'potato' is not a valid address

        >>> type(e)
        <class 'brownie.convert.EthAddress'>

Fixed
-----

.. py:class:: brownie.convert.datatypes.Fixed(value)

    :py:class:`decimal.Decimal <decimal.Decimal>` subclass that allows comparisons, addition and subtraction against strings, integers and :func:`Wei <brownie.convert.datatypes.Wei>`.

    ``Fixed`` is used for inputs and outputs to Vyper contracts that use the `decimal type <https://vyper.readthedocs.io/en/latest/types.html#decimals>`_.

    Attempting comparisons or arithmetic against a float raises a ``TypeError``.

    .. code-block:: python

        >>> from brownie import Fixed
        >>> Fixed(1)
        Fixed('1')
        >>> Fixed(3.1337)
        Traceback (most recent call last):
          File "<console>", line 1, in <module>
        TypeError: Cannot convert float to decimal - use a string instead

        >>> Fixed("3.1337")
        Fixed('3.1337')
        >>> Fixed("12.49 gwei")
        Fixed('12490000000')
        >>> Fixed("-1.23") == -1.2300
        Traceback (most recent call last):
          File "<console>", line 1, in <module>
        TypeError: Cannot compare to floating point - use a string instead

        >>> Fixed("-1.23") == "-1.2300"
        True

HexString
---------

.. py:class:: brownie.convert.datatypes.HexString(value, type_)

    Bytes subclass for hexstring comparisons. Raises ``TypeError`` if compared to a non-hexstring. Evaluates ``True`` for hex strings with the same value but differing leading zeros or capitalization.

    All ``bytes`` values returned from a contract call or as part of an event log are given in this type.

    .. code-block:: python

        >>> from brownie.convert import HexString
        >>> h = HexString("0x00abcd", "bytes2")
        "0xabcd"
        >>> h == "0xabcd"
        True
        >>> h == "0x0000aBcD"
        True
        >>> h == "potato"
        Traceback (most recent call last):
          File "<console>", line 1, in <module>
        TypeError: Invalid type for comparison: 'potato' is not a valid hex string

ReturnValue
-----------

.. py:class:: brownie.convert.datatypes.ReturnValue

    Tuple subclass with limited `dict <https://docs.python.org/3/library/stdtypes.html#mapping-types-dict>`_-like functionality. Used for iterable return values from contract calls or event logs.

    .. code-block:: python

        >>> result = issuer.getCountry(784)
        >>> result
        (1, (0, 0, 0, 0), (100, 0, 0, 0))
        >>> result[2]
        (100, 0, 0, 0)
        >>> result.dict()
        {
            '_count': (0, 0, 0, 0),
            '_limit': (100, 0, 0, 0),
            '_minRating': 1
        }
        >>> result['_minRating']
        1

    When checking equality, :func:`ReturnValue <brownie.convert.datatypes.ReturnValue>` objects ignore the type of container compared against. Tuples and lists will both return ``True`` so long as they contain the same values.

    .. code-block:: python

        >>> result = issuer.getCountry(784)
        >>> result
        (1, (0, 0, 0, 0), (100, 0, 0, 0))
        >>> result == (1, (0, 0, 0, 0), (100, 0, 0, 0))
        True
        >>> result == [1, [0, 0, 0, 0], [100, 0, 0, 0]]
        True

.. py:classmethod:: ReturnValue.dict

    Returns a ``dict`` of the named values within the object.

.. py:classmethod:: ReturnValue.items

    Returns a set-like object providing a view on the object's named items.

.. py:classmethod:: ReturnValue.keys

    Returns a set-like object providing a view on the object's keys.

Wei
---

.. py:class:: brownie.convert.datatypes.Wei(value)

    Integer subclass that converts a value to wei (the smallest unit of Ether, equivalent to 10\ :superscript:`-18` Ether) and allows comparisons, addition and subtraction using the same conversion.

    :func:`Wei <brownie.convert.datatypes.Wei>` is useful for strings where you specify the unit, for large floats given in scientific notation, or where a direct conversion to ``int`` would cause inaccuracy from floating point errors.

    Whenever a Brownie method takes an input referring to an amount of ether, the given value is converted to :func:`Wei <brownie.convert.datatypes.Wei>`. Balances and ``uint``/``int`` values returned in contract calls and events are given in :func:`Wei <brownie.convert.datatypes.Wei>`.

    .. code-block:: python

        >>> from brownie import Wei
        >>> Wei("1 ether")
        1000000000000000000
        >>> Wei("12.49 gwei")
        12490000000
        >>> Wei("0.029 shannon")
        29000000
        >>> Wei(8.38e32)
        838000000000000000000000000000000
        >>> Wei(1e18) == "1 ether"
        True
        >>> Wei("1 ether") < "2 ether"
        True
        >>> Wei("1 ether") - "0.75 ether"
        250000000000000000

.. py:classmethod:: Wei.to(unit)

    Returns a :class:`Fixed <brownie.convert.datatypes.Fixed>` number converted to the specified unit.

    Attempting a conversion to an unknown unit raises a ``TypeError``.

    .. code-block:: python

        >>> from brownie import Wei
        >>> Wei("20 gwei").to("ether")
        Fixed('2.0000000000E-8')

``brownie.convert.normalize``
=============================

The ``normalize`` module contains methods used to convert multiple values based on a contract ABI specification. Values are formatted via calls to the methods outlined under :ref:`type conversions<type-conversions>`, and :ref:`type classes<type-classes>` are applied where appropriate.

.. py:method:: normalize.format_input(abi, inputs)

    Formats inputs based on a contract method ABI.

    * ``abi``: A contract method ABI as a dict.
    * ``inputs``: List or tuple of values to format. Each value is converted using one of the methods outlined in :ref:`type-conversions`.

    Returns a list of values formatted for use by ``ContractTx`` or ``ContractCall``.

    .. code-block:: python

        >>> from brownie.convert.normalize import format_input
        >>> abi = {'constant': False, 'inputs': [{'name': '_to', 'type': 'address'}, {'name': '_value', 'type': 'uint256'}], 'name': 'transfer', 'outputs': [{'name': '', 'type': 'bool'}], 'payable': False, 'stateMutability': 'nonpayable', 'type': 'function'}
        >>> format_input(abi, ["0xB8c77482e45F1F44dE1745F52C74426C631bDD52","1 ether"])
        ('0xB8c77482e45F1F44dE1745F52C74426C631bDD52', 1000000000000000000)

.. py:method:: normalize.format_output(abi, outputs)

    Standardizes outputs from a contract call based on the contract's ABI.

    * ``abi``: A contract method ABI as a dict.
    * ``outputs``: List or tuple of values to format.

    Returns a :func:`ReturnValue <brownie.convert.datatypes.ReturnValue>` container where each value has been formatted using the one of the methods outlined in :ref:`type-conversions`.

    This method is used internally by ``ContractCall`` to ensure that contract output formats remain consistent, regardless of the RPC client being used.

    .. code-block:: python

        >>> from brownie.convert.normalize import format_output
        >>> abi = {'constant': True, 'inputs': [], 'name': 'name', 'outputs': [{'name': '', 'type': 'string'}], 'payable': False, 'stateMutability': 'view', 'type': 'function'}
        >>> format_output(abi, ["0x5465737420546f6b656e"])
        ('Test Token',)

.. py:method:: normalize.format_event(event)

    Standardizes outputs from an event fired by a contract.

    * ``event``: Decoded event data as given by the ``decode_event`` or ``decode_trace`` methods of the `eth-event <https://github.com/iamdefinitelyahuman/eth-event>`_ package.

    The given event data is mutated in-place and returned. If an event topic is indexed, the type is changed to ``bytes32`` and ``" (indexed)"`` is appended to the name.

``brownie.convert.utils``
=========================

The ``utils`` module contains helper methods used by other methods within the ``convert`` package.

.. py:method:: utils.get_int_bounds(type_str)

    Given an integer type string, returns the lower and upper bound for that data type.

.. py:method:: utils.get_type_strings(abi_params, substitutions)

    Converts a list of parameters from an ABI into a list of type strings.
