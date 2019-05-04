.. _api-types:

=========
Types API
=========

``brownie.types``
=================

The ``types`` package contains methods relating to data conversion, as well as data types that are unique to Brownie.

``brownie.types.convert``
=========================

The ``convert`` module contains methods relating to data conversion.

Formatting Contract Arguments
-----------------------------

.. py:method:: brownie.types.convert.format_input(abi, inputs)

    Formats inputs based on a contract method ABI.

    * ``abi``: A contract method ABI as a dict.
    * ``inputs``: List or tuple of values to format.

    Returns a list of values formatted for use by ``ContractTx`` or ``ContractCall``.

    Each value in ``inputs`` is converted using the one of the methods outlined in :ref:`type-conversions`.

    .. code-block:: python

        >>> from brownie.types.convert import format_input
        >>> format_input({"constant":False,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[],"payable":False,"type":"function"},["0xB8c77482e45F1F44dE1745F52C74426C631bDD52","1 ether"])
        ['0xB8c77482e45F1F44dE1745F52C74426C631bDD52', 1000000000000000000]

.. py:method:: brownie.types.convert.format_output(value)

    Converts output from a contract call into a more human-readable format.

    .. code-block:: python

        >>> from brownie.types.convert import format_output
        >>> format_output([b'\xaa\x00\x13'])
        ('0xaa0013',)

.. _type-conversions:

Type Conversions
----------------

The following methods are used to convert arguments supplied to ``ContractTx`` and ``ContractCall``.

.. _wei:

.. py:method:: brownie.types.convert.wei(value)

    Converts a value to an integer in wei. Useful for strings where you specify the unit, or for large floats given in scientific notation, where a direct conversion to ``int`` would cause inaccuracy from floating point errors.

    ``wei`` is automatically applied in all Brownie methods when an input is meant to specify an amount of ether.

    .. code-block:: python

        >>> from brownie import wei
        >>> wei("1 ether")
        1000000000000000000
        >>> wei("12.49 gwei")
        12490000000
        >>> wei("0.029 shannon")
        29000000
        >>> wei(8.38e32)
        838000000000000000000000000000000

.. py:method:: brownie.types.convert.to_uint(value, type_="uint256")

    Converts a value to an unsigned integer. This is equivalent to calling ``wei`` and then applying checks for over/underflows.

.. py:method:: brownie.types.convert.to_int(value, type_="int256")

    Converts a value to a signed integer. This is equivalent to calling ``wei`` and then applying checks for over/underflows.

.. py:method:: brownie.types.convert.to_bool(value)

    Converts a value to a boolean. Raises ``TypeError`` if the value is not in ``(True, False, 0, 1)``.

.. py:method:: brownie.types.convert.to_address(value)

    Converts a value to a checksummed address. Raises ``ValueError`` if value cannot be converted.

.. py:method:: brownie.types.convert.to_bytes(value, type_="bytes32")

    Converts a value to bytes. ``value`` can be given as bytes, a hex string, or an integer.

    Raises ``OverflowError`` if the length of the converted value exceeds that specified by ``type_``.

    Pads left with ``00`` if the length of the converted value is less than that specified by ``type_``.

    .. code-block:: python

        >>> to_bytes('0xff','bytes')
        b'\xff'
        >>> to_bytes('0xff','bytes16')
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff'

.. py:method:: brownie.types.convert.to_string(value)

    Converts a value to a string encoded to bytes.

``brownie.types.types``
=======================

The ``types`` module contains data types that are unique to Brownie.

StrictDict
----------

.. py:class:: brownie.types.types.StrictDict

    Subclass of `dict <https://docs.python.org/3/library/stdtypes.html#mapping-types-dict>`__ that prevents adding new keys when locked. Used to hold config file settings.

    .. code-block:: python

        >>> from brownie.types import StrictDict
        >>> s = StrictDict({'test': 123})
        >>> s
        {'test': 123}

.. py:classmethod:: StrictDict._lock

    Locks the ``StrictDict``. When locked, attempts to add a new key will raise a ``KeyError``.

    .. code-block:: python

        >>> s._lock()
        >>> s['other'] = True
        Traceback (most recent call last):
        File "brownie/types/types.py", line 18, in __setitem__
          raise KeyError("{} is not a known config setting".format(key))
        KeyError: 'other is not a known config setting'
        >>>

.. py:classmethod:: StrictDict._unlock

    Unlocks the ``StrictDict``. When unlocked, new keys can be added.

    .. code-block:: python

        >>> s._unlock()
        >>> s['other'] = True
        >>> s
        {'test': 123, 'other': True}

FalseyDict
----------

.. py:class:: brownie.types.types.FalseyDict

    Subclass of `dict <https://docs.python.org/3/library/stdtypes.html#mapping-types-dict>`__ that returns ``False`` if a key is not present. Used by ``brownie._config`` for command-line flags.

.. py:classmethod:: FalseyDict._update_from_args(values)

    Parses command line arguments as  returned from `docopt(__doc__) <https://github.com/docopt/docopt>`__ and adds them to the object.

KwargTuple
----------

.. py:class:: brownie.types.types.KwargTuple

    Hybrid container type with similaries to both `tuple <https://docs.python.org/3/library/stdtypes.html#tuples>`__ and `dict <https://docs.python.org/3/library/stdtypes.html#mapping-types-dict>`__. Used for contract return values.

    .. code-block:: python

        >>> k = issuer.getCountry(784)
        >>> k
        (1, (0, 0, 0, 0, 0, 0, 0, 0), (100, 0, 0, 0, 0, 0, 0, 0))
        >>> k[2]
        (100, 0, 0, 0, 0, 0, 0, 0)
        >>> k.dict()
        {
            '_count': (0, 0, 0, 0, 0, 0, 0, 0),
            '_limit': (100, 0, 0, 0, 0, 0, 0, 0),
            '_minRating': 1
        }
        >>> k['_minRating']
        1

.. py:classmethod:: KwargTuple.copy

    Returns a shallow copy of the object.

.. py:classmethod:: KwargTuple.count(value)

    Returns the number of occurances of ``value`` within the object.

.. py:classmethod:: KwargTuple.dict

    Returns a ``dict`` of the named values within the object.

.. py:classmethod:: KwargTuple.index(value, [start, [stop]])

    Returns the first index of ``value``. Raises ``ValueError`` if the value is not present.

.. py:classmethod:: KwargTuple.items

    Returns a set-like object providing a view on the object's named items.

.. py:classmethod:: KwargTuple.keys

    Returns a set-like object providing a view on the object's keys.

.. _api-types-eventdict:

EventDict
---------

.. py:class:: brownie.types.types.EventDict

    Hybrid container type that works as a `dict <https://docs.python.org/3/library/stdtypes.html#mapping-types-dict>`__ and a `list <https://docs.python.org/3/library/stdtypes.html#lists>`__. Base class, used to hold all events that are fired in a transaction.

    When accessing events inside the object:

    * If the key is given as an integer, events are handled as a list in the order that they fired. An ``_EventItem`` is returned for the specific event that fired at the given position.
    * If the key is given as a string, a ``_EventItem`` is returned that contains all the events with the given name.

    .. code-block:: python

        >>> tx
        <Transaction object '0xf1806643c21a69fcfa29187ea4d817fb82c880bcd7beee444ef34ea3b207cebe'>
        >>> tx.events
        {
            'CountryModified': [
                {
                    'country': 1,
                    'limits': (0, 0, 0, 0, 0, 0, 0, 0),
                    'minrating': 1,
                    'permitted': True
                },
                    'country': 2,
                    'limits': (0, 0, 0, 0, 0, 0, 0, 0),
                    'minrating': 1,
                    'permitted': True
                }
            ],
            'MultiSigCallApproved': {
                'callHash': "0x0013ae2e37373648c5161d81ca78d84e599f6207ad689693d6e5938c3ae4031d",
                'caller': "0xf9c1fd2f0452fa1c60b15f29ca3250dfcb1081b9"
            }
        }
        >>> tx.events['CountryModified']
        [
            {
                'country': 1,
                'limits': (0, 0, 0, 0, 0, 0, 0, 0),
                'minrating': 1,
                'permitted': True
            },
                'country': 2,
                'limits': (0, 0, 0, 0, 0, 0, 0, 0),
                'minrating': 1,
                'permitted': True
            }
        ]
        >>> tx.events[0]
        {
            'callHash': "0x0013ae2e37373648c5161d81ca78d84e599f6207ad689693d6e5938c3ae4031d",
            'caller': "0xf9c1fd2f0452fa1c60b15f29ca3250dfcb1081b9"
        }

.. py:classmethod:: EventDict.count(name)

    Returns the number of events that fired with the given name.

    .. code-block:: python

        >>> tx.events.count('CountryModified')
        2

.. py:classmethod:: EventDict.items

    Returns a set-like object providing a view on the object's items.

.. py:classmethod:: EventDict.keys

    Returns a set-like object providing a view on the object's keys.

.. py:classmethod:: EventDict.values

    Returns an object providing a view on the object's values.

_EventItem
----------

.. py:class:: brownie.types.types._EventItem

    Hybrid container type that works as a `dict <https://docs.python.org/3/library/stdtypes.html#mapping-types-dict>`__ and a `list <https://docs.python.org/3/library/stdtypes.html#lists>`__. Represents one or more events with the same name that were fired in a transaction.

    Instances of this class are created by ``EventDict``, it is not intended to be instantiated directly.

    When accessing events inside the object:

    * If the key is given as an integer, events are handled as a list in the order that they fired. An ``_EventItem`` is returned for the specific event that fired at the given position.
    * If the key is given as a string, ``_EventItem`` assumes that you wish to access the first event contained within the object. ``event['value']`` is equivalent to ``event[0]['value']``.

    .. code-block:: python

        >>> event = tx.events['CountryModified']
        <Transaction object '0xf1806643c21a69fcfa29187ea4d817fb82c880bcd7beee444ef34ea3b207cebe'>
        >>> event
        [
            {
                'country': 1,
                'limits': (0, 0, 0, 0, 0, 0, 0, 0),
                'minrating': 1,
                'permitted': True
            },
                'country': 2,
                'limits': (0, 0, 0, 0, 0, 0, 0, 0),
                'minrating': 1,
                'permitted': True
            }
        ]
        >>> event[0]
        {
            'country': 1,
            'limits': (0, 0, 0, 0, 0, 0, 0, 0),
            'minrating': 1,
            'permitted': True
        }
        >>> event['country']
        1
        >>> event[1]['country']
        2

.. py:attribute:: _EventItem.name

    The name of the event(s) contained within this object.

    .. code-block:: python

        >>> tx.events[2].name
        CountryModified


.. py:attribute:: _EventItem.pos

    A tuple giving the absolute position of each event contained within this object.

    .. code-block:: python

        >>> event.pos
        (1, 2)
        >>> event[1].pos
        (2,)
        >>> tx.events[2] == event[1]
        True

.. py:classmethod:: _EventItem.items

    Returns a set-like object providing a view on the items in the first event within this object.

.. py:classmethod:: _EventItem.keys

    Returns a set-like object providing a view on the keys in the first event within this object.

.. py:classmethod:: _EventItem.values

    Returns an object providing a view on the values in the first event within this object.

.. _api-types-singleton:

_Singleton
----------

.. py:class:: brownie.types.types._Singleton

Internal metaclass used to create `singleton <https://en.wikipedia.org/wiki/Singleton_pattern>`__ objects. Instantiating a class derived from this metaclass will always return the same instance, regardless of how the child class was imported.
