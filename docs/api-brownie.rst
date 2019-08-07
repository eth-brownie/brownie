.. _api-brownie:

===========
Brownie API
===========

``brownie``
===========

The ``brownie`` package is the main package containing all of Brownie's functionality.

.. code-block:: python

    >>> from brownie import *
    >>> dir()
    ['Gui', 'accounts', 'alert', 'brownie', 'check', 'compile_source', 'config', 'history', 'network', 'project', 'rpc', 'web3', 'wei']

.. _api-brownie-convert:

``brownie.convert``
===================

The ``convert`` module contains methods relating to data conversion.

Formatting Contract Data
************************

The following methods are used to convert multiple values based on a contract ABI specification. Values are formatted via calls to the methods outlined under :ref:`type conversions<type-conversions>`, and where appropriate :ref:`type classes<type-classes>` are applied.

.. py:method:: brownie.convert.format_input(abi, inputs)

    Formats inputs based on a contract method ABI.

    * ``abi``: A contract method ABI as a dict.
    * ``inputs``: List or tuple of values to format.

    Returns a list of values formatted for use by ``ContractTx`` or ``ContractCall``.

    Each value in ``inputs`` is converted using the one of the methods outlined in :ref:`type-conversions`.

    .. code-block:: python

        >>> from brownie.convert import format_input
        >>> abi = {'constant': False, 'inputs': [{'name': '_to', 'type': 'address'}, {'name': '_value', 'type': 'uint256'}], 'name': 'transfer', 'outputs': [{'name': '', 'type': 'bool'}], 'payable': False, 'stateMutability': 'nonpayable', 'type': 'function'}
        >>> format_input(abi, ["0xB8c77482e45F1F44dE1745F52C74426C631bDD52","1 ether"])
        ['0xB8c77482e45F1F44dE1745F52C74426C631bDD52', 1000000000000000000]

.. py:method:: brownie.convert.format_output(abi, outputs)

    Standardizes outputs from a contract call based on the contract's ABI.

    * ``abi``: A contract method ABI as a dict.
    * ``outputs``: List or tuple of values to format.

    Each value in ``outputs`` is converted using the one of the methods outlined in :ref:`type-conversions`.

    This method is called internally by ``ContractCall`` to ensure that contract output formats remain consistent, regardless of the RPC client being used.

    .. code-block:: python

        >>> from brownie.convert import format_output
        >>> abi = {'constant': True, 'inputs': [], 'name': 'name', 'outputs': [{'name': '', 'type': 'string'}], 'payable': False, 'stateMutability': 'view', 'type': 'function'}
        >>> format_output(abi, ["0x5465737420546f6b656e"])
        ["Test Token"]

.. py:method:: brownie.convert.format_event(event)

    Standardizes outputs from an event fired by a contract.

    * ``event``: Decoded event data as given by the ``decode_event`` or ``decode_trace`` methods of the `eth-event <https://github.com/iamdefinitelyahuman/eth-event>`__ package.

    The given event data is mutated in-place and returned. If an event topic is indexed, the type is changed to ``bytes32`` and ``" (indexed)"`` is appended to the name.

.. _type-conversions:

Type Conversions
****************

The following classes and methods are used to convert arguments supplied to ``ContractTx`` and ``ContractCall``.


.. py:method:: brownie.convert.to_uint(value, type_="uint256")

    Converts a value to an unsigned integer. This is equivalent to calling ``Wei`` and then applying checks for over/underflows.

.. py:method:: brownie.convert.to_int(value, type_="int256")

    Converts a value to a signed integer. This is equivalent to calling ``Wei`` and then applying checks for over/underflows.

.. py:method:: brownie.convert.to_bool(value)

    Converts a value to a boolean. Raises ``ValueError`` if the given value does not match a value in ``(True, False, 0, 1)``.

.. py:method:: brownie.convert.to_address(value)

    Converts a value to a checksummed address. Raises ``ValueError`` if value cannot be converted.

.. py:method:: brownie.convert.to_bytes(value, type_="bytes32")

    Converts a value to bytes. ``value`` can be given as bytes, a hex string, or an integer.

    Raises ``OverflowError`` if the length of the converted value exceeds that specified by ``type_``.

    Pads left with ``00`` if the length of the converted value is less than that specified by ``type_``.

    .. code-block:: python

        >>> to_bytes('0xff','bytes')
        b'\xff'
        >>> to_bytes('0xff','bytes16')
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff'

.. py:method:: brownie.convert.to_string(value)

    Converts a value to a string.

.. py:method:: brownie.convert.bytes_to_hex(value)

    Converts a bytes value to a hex string.

    .. code-block:: python

        >>> from brownie.convert import bytes_to_hex
        >>> bytes_to_hex(b'\xff\x3a')
        0xff3a
        >>> bytes_to_hex('FF')
        0xFF
        >>> bytes_to_hex("Hello")
          File "brownie/types/convert.py", line 149, in bytes_to_hex
            raise ValueError("'{}' is not a valid hex string".format(value))
        ValueError: 'Hello' is not a valid hex string

.. _type-classes:

Type Classes
************

For certain types of contract data, Brownie uses subclasses to assist with conversion and comparison.

.. _wei:

.. py:class:: brownie.convert.Wei(value)

    Integer subclass that converts a value to wei and allows comparisons, addition and subtraction using the same conversion.

    ``Wei`` is useful for strings where you specify the unit, for large floats given in scientific notation, or where a direct conversion to ``int`` would cause inaccuracy from floating point errors.

    Whenever a Brownie method takes an input referring to an amount of ether, the given value is converted to ``Wei``. Balances and ``uint``/``int`` values returned in contract calls and events are given in ``Wei``.

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

.. py:class:: brownie.convert.EthAddress(value)

    String subclass for address comparisons. Raises a ``TypeError`` when compared to a non-address.

    Addresses returned from a contract call or as part of an event log are given in this type.

    .. code-block:: python

        >>> from brownie.convert import EthAddress
        >>> e = EthAddress("0x0035424f91fd33084466f402d5d97f05f8e3b4af")
        "0x0035424f91fd33084466f402d5d97f05f8e3b4af"
        >>> e == "0x3506424F91fD33084466F402d5D97f05F8e3b4AF"
        False
        >>> e == "0x0035424F91fD33084466F402d5D97f05F8e3b4AF"
        True
        >>> e == "0x35424F91fD33084466F402d5D97f05F8e3b4AF"
        Traceback (most recent call last):
        File "brownie/convert.py", line 304, in _address_compare
            raise TypeError(f"Invalid type for comparison: '{b}' is not a valid address")
        TypeError: Invalid type for comparison: '0x35424F91fD33084466F402d5D97f05F8e3b4AF' is not a valid address

        >>> e == "potato"
        Traceback (most recent call last):
        File "brownie/convert.py", line 304, in _address_compare
            raise TypeError(f"Invalid type for comparison: '{b}' is not a valid address")
        TypeError: Invalid type for comparison: 'potato' is not a valid address

.. py:class:: brownie.convert.HexString(value, type_)

    Bytes subclass for hexstring comparisons. Raises ``TypeError`` if compared to a non-hexstring. Evaluates ``True`` for hex strings with the same value but differing leading zeros or capitalization.

    All ``bytes`` values returned from a contract call or as part of an event log are given in this type.

    .. code-block:: python

        >>> h = HexString("0x00abcd", "bytes2")
        "0xabcd"
        >>> h == "0xabcd"
        True
        >>> h == "0x0000aBcD"
        True
        >>> h == "potato"
        File "<console>", line 1, in <module>
        File "brownie/convert.py", line 327, in _hex_compare
          raise TypeError(f"Invalid type for comparison: '{b}' is not a valid hex string")
        TypeError: Invalid type for comparison: 'potato' is not a valid hex string

.. _return_value:

.. py:class:: brownie.network.return_value.ReturnValue

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

    When checking equality, ``ReturnValue`` objects ignore the type of container compared against. Tuples and lists will both return ``True`` so long as they contain the same values.

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

``brownie.exceptions``
======================

The ``exceptions`` module contains all Brownie ``Exception`` classes.

network
*******

.. py:exception:: brownie.exceptions.UnknownAccount

    Raised when the ``Accounts`` container cannot locate a specified ``Account`` object.

.. py:exception:: brownie.exceptions.UndeployedLibrary

    Raised when attempting to deploy a contract that requires an unlinked library, but the library has not yet been deployed.

.. py:exception:: brownie.exceptions.IncompatibleEVMVersion

    Raised when attempting to deploy a contract that was compiled to target an EVM version that is imcompatible than the currently active local RPC client.

.. py:exception:: brownie.exceptions.RPCConnectionError

    Raised when the RPC process is active and ``web3`` is connected, but Brownie is unable to communicate with it.

.. py:exception:: brownie.exceptions.RPCProcessError

    Raised when the RPC process fails to launch successfully.

.. py:exception:: brownie.exceptions.RPCRequestError

    Raised when a direct request to the RPC client has failed, such as a snapshot or advancing the time.

.. py:exception:: brownie.exceptions.VirtualMachineError

    Raised when a contract call causes the EVM to revert.

project
*******

.. py:exception:: brownie.exceptions.ContractExists

    Raised by ``project.compile_source`` when the source code contains a contract with a name that is the same as a contract in the active project.

.. py:exception:: brownie.exceptions.ProjectAlreadyLoaded

    Raised by ``project.load_project`` if a project has already been loaded.

.. py:exception:: brownie.exceptions.ProjectNotFound

    Raised by ``project.load_project`` when a project cannot be found at the given path.

.. py:exception:: brownie.exceptions.CompilerError

    Raised by the compiler when there is an error within a contract's source code.

.. py:exception:: brownie.exceptions.IncompatibleSolcVersion

    Raised when a project requires a version of solc that is not installed or not supported by Brownie.

.. py:exception:: brownie.exceptions.PragmaError

    Raised when a contract has no pragma directive, or a pragma which requires a version of solc that cannot be installed.

``brownie._config``
===================

The ``_config`` module handles all Brownie configuration settings. It is not designed to be accessed directly. If you wish to view or modify config settings while Brownie is running, import ``brownie.config`` which will return a ``ConfigDict`` with the active settings:

.. code-block:: python

    >>> from brownie import config
    >>> type(config)
    <class 'brownie._config.ConfigDict'>
    >>> config['network_defaults']
    {'name': 'development', 'gas_limit': False, 'gas_price': False}

.. _api-types-configdict:

ConfigDict
**********

.. py:class:: brownie.types.types.ConfigDict

    Subclass of `dict <https://docs.python.org/3/library/stdtypes.html#mapping-types-dict>`__ that prevents adding new keys when locked. Used to hold config file settings.

    .. code-block:: python

        >>> from brownie.types import ConfigDict
        >>> s = ConfigDict({'test': 123})
        >>> s
        {'test': 123}

.. py:classmethod:: ConfigDict._lock

    Locks the ``ConfigDict``. When locked, attempts to add a new key will raise a ``KeyError``.

    .. code-block:: python

        >>> s._lock()
        >>> s['other'] = True
        Traceback (most recent call last):
        File "brownie/types/types.py", line 18, in __setitem__
          raise KeyError("{} is not a known config setting".format(key))
        KeyError: 'other is not a known config setting'
        >>>

.. py:classmethod:: ConfigDict._unlock

    Unlocks the ``ConfigDict``. When unlocked, new keys can be added.

    .. code-block:: python

        >>> s._unlock()
        >>> s['other'] = True
        >>> s
        {'test': 123, 'other': True}

.. _api-types-singleton:

``brownie._singleton``
======================

.. py:class:: brownie.types.types._Singleton

Internal metaclass used to create `singleton <https://en.wikipedia.org/wiki/Singleton_pattern>`__ objects. Instantiating a class derived from this metaclass will always return the same instance, regardless of how the child class was imported.
